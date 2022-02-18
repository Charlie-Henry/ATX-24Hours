from datetime import datetime, timedelta
import os
import argparse

import boto3
import imageio
import requests
from dotenv import load_dotenv
from prefect import task, Flow, Parameter
from prefect.schedules import IntervalSchedule


# Envriomnent variables
load_dotenv("modalshift.env")

AWS_ACCESS_ID = os.environ.get("AWS_ACCESS_ID")
AWS_PASS = os.environ.get("AWS_PASS")
BUCKET_NAME = os.environ.get("BUCKET_NAME")

client = aws_s3_client = boto3.client(
    "s3", aws_access_key_id=AWS_ACCESS_ID, aws_secret_access_key=AWS_PASS,
)


@task
def get_image(camera):
    """
    Goes to the CCTV snapshot endpoint and downloads the file to disk.

    Parameters
    ----------
    camera : int
        ID of camera used in the endpoint.

    Returns
    -------
    None.

    """
    # Getting screenshot
    url = f"https://cctv.austinmobility.io/image/{camera}.jpg"
    r = requests.get(url, allow_redirects=False)

    # Naming the file
    name = datetime.now().strftime("%Y-%m-%d %H%M%S")
    name = f"{name}.jpg"
    save_path = f"{os.getcwd()}/{camera}"
    completeName = os.path.join(save_path, name)

    # Saving
    file1 = open(completeName, "wb")
    file1.write(r.content)

    # Checking if more than 24 hours of screenshots are already in the folder.
    #   Drops the oldest if there is.
    os.chdir(str(camera))
    filenames = os.listdir()
    filenames = [f for f in filenames if f.endswith(".jpg")]

    if len(filenames) > 288:
        oldest_file = min(filenames, key=os.path.getctime)
        os.remove(oldest_file)

    os.chdir("../")

    return


@task
def build_gif(camera):
    """
    Complies a gif based on the screenshots, compresses it, and sends to an S3 bucket. 

    Parameters
    ----------
    camera : int
        ID of camera used in the endpoint and file structure.

    Returns
    -------
    None.

    """
    os.chdir(str(camera))
    filenames = os.listdir()

    # Get a list of images
    filenames = [f for f in filenames if f.endswith(".jpg")]
    filenames.sort()
    images = []
    for filename in filenames:
        images.append(imageio.imread(filename))
    # Create uncompressed gif
    imageio.mimsave(f"{camera}_animated.gif", images, duration=0.1)

    # gif compression to max size 1MB
    os.chdir("../")
    cli = f"python lin.py {os.getcwd()}/{camera}/{camera}_animated.gif"
    os.system(cli)

    os.chdir(str(camera))
    os.chdir("output")

    # Upload that file to S3
    client.upload_file(
        f"{camera}_animated.gif",
        BUCKET_NAME,
        f"{camera}_animated.gif",
        ExtraArgs={"ContentType": "image/gif"},
    )

    os.chdir("../")
    os.chdir("../")


def build_flow(schedule=None):
    with Flow("charlie_etl", schedule=schedule) as flow:
        cameras = Parameter(name="camera_ids", default=[145, 51])
        get_image.map(cameras)
        build_gif.map(cameras)
    return flow


schedule = IntervalSchedule(
    start_date=datetime.now() + timedelta(seconds=1), interval=timedelta(minutes=5),
)

flow = build_flow(schedule)
# Flow.run parameters is the list of camera IDs, currently defaults to 145 and 51
flow.run(parameters={"camera_ids": [145, 51, 39]})

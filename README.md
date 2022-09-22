# Sentinel Downloading & Viewing Files

## Sentinel_Download.ipynb

This notebook was for experimenting with ways to download and unzip Sentinel3 image data.

## Sentinel_View.ipynb

This notebook allowed for unzipped files from Sentinel_Download.ipynb to be viewed.
- Uses a function to calculate the Width and Height of an exported image using the swath size and Sentinel resolution

## Sentinel_DownloadView.ipynb

Combines the previous two notebooks into 1 function to make exporting easier.

## SentinelExp.py

A python script with the function made in Sentinel_DownloadView.ipynb used for a SBATCH Job
- Includes a date range function to make exporting data over a series of time easier

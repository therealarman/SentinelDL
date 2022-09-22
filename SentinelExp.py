import eumdac
import datetime
import shutil
from datetime import timedelta
from sentinelsat import read_geojson, geojson_to_wkt
import zipfile
import gzip
import os
import pandas as pd
from glob import glob
from satpy import Scene, find_files_and_readers
from satpy.writers import get_enhanced_image
from pyresample import create_area_def
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import numpy as np

os.chdir('/mnt/beegfs/home/alexisa2019/Projects/SentinelProject')
print(os.getcwd())

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def get_datastore(consumer_key, consumer_secret):
    token = eumdac.AccessToken((consumer_key, consumer_secret))
    print(f"This token '{token}' expires {token.expiration}")
    return eumdac.DataStore(token)

# How to figure out a good pixel extent

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def Sentinel_request(datastore, roi, lon1, lon2, lat1, lat2,
                     collectionID='EO:EUM:DAT:0409',
                     opath = './',
                     start_date = None, end_date = None, suffix = None):
    
    if(suffix == None):
        suffix = f"{str(lon1)}_{str(lat1)}"

    WKT = 'POLYGON(({}))'.format(','.join(["{} {}".format(*coord) for coord in roi]))
    selected_collection = datastore.get_collection(collectionID)
    print(selected_collection.title)
    
    if(end_date == None):
        end_date = datetime.date.today()
    if(start_date == None):
        start_date = end_date-timedelta(days=1)
        
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    print('Searching from %s to %s' %(start_date, end_date))
    products = selected_collection.search(geo=WKT, 
                                          dtstart=start_date, 
                                          dtend=end_date)
    print(f'Found Datasets: {len(products)} datasets for the given time range')
    for product in products:
        with product.open() as fsrc, open(opath+fsrc.name, mode='wb') as fdst:
            if os.path.getsize(fdst.name)>0:

                print(f'Product {fdst.name} exists.')
            else:
                shutil.copyfileobj(fsrc, fdst)
                print(f'Download of product {product} finished.')
    print('All downloads are finished.')
            
    rpath = opath+'S3_%s_%s' % (start_date.strftime("%Y%m%d"),
                                start_date.strftime("%Y%m%d"))                    
    for f in glob(opath+'S3*.zip'):
        try:
            with zipfile.ZipFile(f, 'r') as zip_ref:
                print('Unziping %s' %f)
                zip_ref.extractall(rpath)
                os.remove(f)
        except:
            print('Bad zip file: %s' %f)

    print(f'Done! Files in {rpath}')
    
    # VISUALIZING...
    
    print("Starting visualization :D")
    
    try:    
        files = find_files_and_readers(sensor='olci',
                                   start_time=start_date,
                                   end_time=end_date,
                                   base_dir = rpath,
                                   reader='olci_l1b')

        scn = Scene(filenames=files)
        scn.load(['true_color'])

        meanWidth = .5*(haversine(lon1, lat1, lon2, lat1)+haversine(lon1, lat2, lon2, lat2))

        height = haversine(lon1, lat1, lon1, lat2)

        pixWidth = (int(meanWidth) * 1000) / 300
        pixHeight = (int(height) * 1000) / 300

        print(f"Width: {meanWidth}, Height: {height}")
        print(f"%Width: {pixWidth}, %Height: {pixHeight}")

        my_area = create_area_def('my_area', {'proj': 'lcc', 'lon_0': -91., 'lat_0': 29.5, 'lat_1': 29.5, 'lat_2': 29.5},
                              width=pixWidth, height=pixHeight,
                              area_extent=[lon1, lat1, lon2, lat2], units='degrees')
        new_scn = scn.resample(my_area)
        #generate RGB from true color
        rgb = get_enhanced_image(new_scn['true_color'])
        #extract projection and lon lat from products
        crs = new_scn['true_color'].attrs['area'].to_cartopy_crs()

        fig =  plt.figure(figsize=(6, 4), dpi=400)
        ax1 = plt.subplot(projection=crs)
        rgb.data.plot.imshow(rgb='bands', transform=crs, ax=ax1)
        ax1.set_title('Sentinel3_%s_%s' % (new_scn.start_time.isoformat(), suffix))

        #save figure
        fig.savefig('Sentinel3_%s_%s_rgb.png' % (new_scn.start_time.isoformat(), suffix))
    except:
        print(f"Could not generate image for {rpath}")

consumer_key = 'yawsJIqGoAetBf_MqpcByUwnrWMa'
consumer_secret = 'w6nWuFAtEgPhFESfK7Q4MzOs9t0a'
datastore = get_datastore(consumer_key, consumer_secret)

today = datetime.datetime.now()
yesterday = today - timedelta(days=1)

#FL Bay Export

roi = [[-81.0955810546875,26.675685969067487],
       [-80.54489135742188,26.675685969067487],
       [-80.54489135742188,27.243641579169292],
       [-81.0955810546875,27.243641579169292],
       [-81.0955810546875,26.675685969067487]]

lon1 = -82
lat1 = 26
lon2 = -80
lat2 = 24

loop_start_date = datetime.date(2022, 8, 31)
loop_end_date = datetime.date(2022, 9, 10)
for single_date in daterange(loop_start_date, loop_end_date):
    print(single_date.strftime("%Y-%m-%d"))
    prevDate = single_date - timedelta(days=1)
    Sentinel_request(datastore, roi, lon1, lon2, lat1, lat2, opath='./products/', start_date=prevDate,
                     end_date=single_date, suffix = "FlBay")

#GOMEX Export

roi = [[-92.054443359375,29.14736383122664],
       [-89.2474365234375,29.14736383122664],
       [-89.2474365234375,30.372875188118016],
       [-92.054443359375,30.372875188118016],
       [-92.054443359375,29.14736383122664]]

lon1 = -92
lat1 = 29
lon2 = -89
lat2 = 30

loop_start_date = datetime.date(2022, 7, 6)
loop_end_date = datetime.date(2022, 7, 28)
for single_date in daterange(loop_start_date, loop_end_date):
    print(single_date.strftime("%Y-%m-%d"))
    prevDate = single_date - timedelta(days=1)
    Sentinel_request(datastore, roi, lon1, lon2, lat1, lat2, opath='./products/', start_date=prevDate,
                     end_date=single_date, suffix = "Gomex")
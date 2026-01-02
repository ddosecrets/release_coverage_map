#!/usr/bin/env python3
import os, csv, requests, json
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import cartopy.io.shapereader as shpreader
import numpy as np
import matplotlib as mpl
import pycountry
from collections import defaultdict
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import cm
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

def getCountries():
	cachefile = "countries.json"
	url = "https://ddosecrets.com/feed/countries.json"
	if( os.path.isfile(cachefile) ):
		with open(cachefile, "r") as f:
			return json.loads(f.read())
	else:
		countries = requests.get(url).text
		with open(cachefile, "w") as f:
			f.write(countries)
		return json.loads(countries)

if __name__ == "__main__":
	mpl.rcParams['figure.figsize'] = [5.12, 3.84]
	mpl.rcParams['figure.dpi'] = 300
	mpl.rcParams['savefig.dpi'] = 300

	# Pre-load a list of "American Samoa" => "AS" conversions
	country_codes = dict()
	for country in pycountry.countries:
		country_codes[country.name] = country.alpha_2
	# Hardcode countries that are officially listed like "Iran (Islamic Republic of)"
	country_codes["Bolivia"] = "BO"
	country_codes["Iran"] = "IR"
	country_codes["Russia"] = "RU"
	country_codes["Syria"] = "SY"
	country_codes["United States of America"] = "US"
	country_codes["Britain"] = "GB"
	country_codes["Venezuela"] = "VE"

	countries = defaultdict(lambda: 0)
	total_hosts = 0
	article_countries = getCountries()
	for (country,count) in article_countries.items():
		try:
			code = country_codes[country]
			countries[code] += int(count)
			total_hosts += int(count)
		except KeyError:
			print("ERROR: No country code for '%s', skipping..." % country)
			pass

	countries_shp = shpreader.natural_earth(resolution='110m',
											category='cultural', name='admin_0_countries')

	#colormap = plt.get_cmap('viridis', 12)
	#colormap = plt.get_cmap('turbo', 12)
	colormap = plt.get_cmap('turbo')
	#norm = mpl.colors.Normalize(vmin=1, vmax=max(countries.values()))
	norm = mpl.colors.PowerNorm(vmin=1, vmax=max(countries.values()), gamma=0.4)

	def getColor(country):
		if( country in countries ):
			count = countries[country]
			return colormap(norm(count))
		return np.array([1,1,1])

	# NOTE: We set the projection at the _axis_ level,
	# but always leave `add_geometries` as PlateCarree.
	# This tells matplotlib to convert from the PlateCarree
	# coordinates to whatever projection we actually want.
	fig,ax = plt.subplots(figsize=(12,6), subplot_kw={"projection":ccrs.Robinson()})
	# Remove the oval border on the map
	ax.set_frame_on(False)
	blank_color = np.array([1,1,1])
	transform_from = ccrs.PlateCarree()._as_mpl_transform(ax)
	for country in shpreader.Reader(countries_shp).records():
		color = getColor(country.attributes['WB_A2'])
		if( np.array_equal(color, blank_color) ):
			ax.add_geometries([country.geometry], ccrs.PlateCarree(),
							  edgecolor='black',
							  linewidth=0.5,
							  facecolor=color,
							  label=country.attributes['CONTINENT'])
		else:
			ax.add_geometries([country.geometry], ccrs.PlateCarree(),
							  facecolor=color,
							  label=country.attributes['CONTINENT'])

	plt.suptitle("Distributed Denial of Secrets\nWorldwide Release Coverage")
	#cax = fig.add_axes([0.95, 0.2, 0.02, 0.6])
	#cbar = mpl.colorbar.ColorbarBase(cax, cmap=colormap, norm=norm, spacing="proportional")
	min_tick = 1
	max_tick = max(countries.values())
	#ticks = list(map(lambda c: int(c), np.linspace(min_tick,max_tick,10)))
	ticks = list(map(lambda c: int(norm.inverse(c)), np.linspace(0,1,12)))
	cax = fig.add_axes([0.2, 0.05, 0.6, 0.02])
	cbar = mpl.colorbar.ColorbarBase(cax, cmap=colormap, norm=norm, orientation="horizontal", ticks=ticks)
	cax.set_xlabel("Datasets Originating in Each Country")

	# Rescale the PNG based on the DPI of current image
	# Trying _really hard_ not to have matplotlib rescale the image
	# because it does a mediocre job 
	array_ddosecrets = mpimg.imread("ddosecrets.png")
	imagebox = OffsetImage(array_ddosecrets, zoom=120./fig.dpi)
	ab = AnnotationBbox(imagebox, (-140,-20), xycoords=transform_from, frameon=False)
	ax.add_artist(ab)

	plt.savefig("releases_per_country.png", bbox_inches='tight')

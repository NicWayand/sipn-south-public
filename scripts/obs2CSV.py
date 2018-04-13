#!/usr/bin/python
#
# Script to convert NetCDF observational references to
# SIPN South compliant format (CSV)
# NSIDC 0081 and OSI-401b
#
# Author - F. Massonnet
# Date   - March 5, 2018

# Imports, modules, etc.
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from datetime import date, timedelta

# Function to compute sea ice area from sea ice concentation
# -----
def compute_area(concentration, cellarea, mask = 1):
  """ Input: - sea ice concentration in %
               numpy array. if 3-D, time is assumed to be 1st
             - cellarea: array of grid cell areas (sq. meters)
             - mask (1 on ocean, 0 on continent)

      Output: Sea ice area in the region defined by the mask
  """
  import sys
  import numpy as np

  if np.max(concentration) < 10.0:
    sys.exit("(compute_area): concentration seems to not be in percent")

  if len(concentration.shape) == 3:
    nt, ny, nx = concentration.shape
    are = np.asarray([np.sum( concentration[jt, :, :] / 100.0 * cellarea * mask) / 1e12 for jt in range(nt)])
  elif len(concentration.shape) == 2:
    are = np.sum( concentration / 100.0 * cellarea * mask) / 1e12
  else:
    sys.exit("(compute_area): concentration has not 2 nor 3 dimensions")

  return are
# ------
# ------
d0 = date(1850, 1, 1)  # Zero-time reference of the input file
d1 = date(2018, 2, 1)  # Start investigated period
d2 = date(2018, 2, 28) # End investigated period (included)

daterange = [d1 + timedelta(days=x) for x in range((d2-d1).days + 1)]

# Input file, following CMIP conventions
filein = "/nas02/CLIMDATA/obs/ice/siconc/nsidc/nsidc0081/processed/native/siconc_r1i1p1_day_20150101-20181231_sh-pss25.nc"

f = Dataset(filein, mode = "r")
siconc = f.variables["siconc"][:]
time   = f.variables["time"][:]
cellarea = f.variables["areacello"][:]
sftof    = f.variables["sftof"][:]
lat      = f.variables["latitude"][:]
lon      = f.variables["longitude"][:]
# Re-range longitude to [0, 360.0]
lon[lon < 0.0] = lon[lon < 0.0] + 360.0
f.close()

# Subset to the month of February 2018
# ------------------------------------
t1 = (d1 - d0).days - time[0]
t2 = (d2 - d0).days - time[0]

# Compute sea ice area for that period
# ------------------------------------
areatot = compute_area(siconc[t1:t2 + 1, :, :], cellarea, mask = 1.0 * (lat < 0.0)) # + 1 because of Python indexing convention

# Save as CSV file
# ----------------
# Total area
with open("./data/txt/obs_" + "000" + "_total-area.txt", "wb") as file:
    file.write(",".join(["{0:.2f}".format(a) for a in areatot]))  
    file.write("\n")

# Per longitude
with open("./data/txt/obs_" + "000" + "_regional-area.txt", "wb") as file:
    # Per longitude bin
    for j_bin in np.arange(36):
      print(j_bin)
      area = compute_area(siconc[t1:t2 + 1, :, :], cellarea, mask = 1.0 * (lat < 0) * (sftof == 100.0) * (lon >= j_bin * 10.0) * (lon < (j_bin + 1) * 10.0))
      file.write(",".join(["{0:.2f}".format(a) for a in area]))  # + 1 as python does not take the last bit
      file.write("\n")

# Plot for internal check
# -----------------------
plt.figure(figsize = (4, 4))
plt.plot(daterange, areatot)
plt.ylim(0.0, 5.0)
plt.savefig("./figs/obs000.png", dpi = 300)


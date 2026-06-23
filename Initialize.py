import wget
import arrow
import schedule
import time
import os
import xarray as xr
import glob
import numpy as np
import os
import subprocess

#https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20250309/00/wave/gridded/gfswave.t00z.global.0p16.f000.grib2

todaysdate = arrow.now().format('YYYYMMDD')

#todaysdate = '20260622'

def get_gfs_grib():

    print("Attempting to execute task downloading the global data at:", time.strftime("%H:%M:%S"))

    output_directory = os.mkdir('{}'.format(todaysdate))

    for i in range(1,24,1):

        print ('DOWNLOADING FORECAST : {:03d}z'.format(i))

        url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{}/00/wave/gridded/gfswave.t00z.global.0p16.f{:03d}.grib2".format(todaysdate, i)

        print ('Downloaded forecast : {}'.format(url))

        filename = wget.download(url, out='{}'.format(todaysdate))

        print ('\n')



def get_bund_valss():

    f = glob.iglob('{}/*.grib2'.format(todaysdate))

    bunds = [101,102,103,104]

    for i in f:

        print ('LOADING GRIB FILE {}'.format(i))

        ds = xr.open_dataset("{}".format(i))

        print ('COMPLETED LOADING GRIB FILE {}'.format(i))

        bund_forcing_swh = []

        bund_forcing_perpw = []

        bund_forcing_dirpw = []

        for k in bunds:

            print('EVALUATING GRIB FILE {} AT  BUND VALUES FOR BUND {}'.format(i, k))

            print ('LOADING THE BUND  FILE {}.csv'.format(k))

            current_bund = np.loadtxt('INITIALISATION/FORCING_BUND_COORDS/{}.csv'.format(k), delimiter=',',skiprows=1)

            bund_all_swh = []

            bund_all_perpw = []

            bund_all_dirpw = []

            for j in current_bund:

                #print (j[2], j[3])

                swh = ds.sel(latitude=j[3], longitude=j[2], method="nearest")['swh'].values

                perpw = ds.sel(latitude=j[3], longitude=j[2], method="nearest")['perpw'].values

                dirpw = ds.sel(latitude=j[3], longitude=j[2], method="nearest")['dirpw'].values

                bund_all_swh.append(swh)

                bund_all_perpw.append(perpw)

                bund_all_dirpw.append(dirpw)

            bund_forcing_swh.append(np.max(bund_all_swh))

            bund_forcing_perpw.append(np.max(bund_all_perpw))

            bund_forcing_dirpw.append(np.max(bund_all_dirpw))

        print ('{} Hs (swell + wind waves) is {}'.format(i ,bund_forcing_swh))

        print ('{} median period (swell + wind waves) is {}'.format(i ,bund_forcing_perpw))

        print ('{} direction (swell + wind waves) is {}'.format(i ,bund_forcing_dirpw))

        bund_forcing_swh = np.array(bund_forcing_swh)

        bund_forcing_perpw = np.array(bund_forcing_perpw)

        bund_forcing_dirpw = np.array(bund_forcing_dirpw)

        np.savetxt('{}_FORCING_swh.csv'.format(i),bund_forcing_swh, delimiter=',' )

        np.savetxt('{}_FORCING_perpw.csv'.format(i),bund_forcing_perpw, delimiter=',' )

        np.savetxt('{}_FORCING_dirpw.csv'.format(i),bund_forcing_dirpw, delimiter=',' )



def get_winds():

    print ("EVALUATING FOR WIND")

    grib_files = glob.iglob('{}/*.grib2'.format(todaysdate))

    for i in grib_files:

        print ("EVALUATING FOR WIND AT GRIB FILE {}".format(i))

        ds = xr.open_dataset("{}".format(i))

        wind_val = ds.sel(latitude=1.90, longitude=73.40, method="nearest")['ws'].values

        wind_dir = ds.sel(latitude=1.90, longitude=73.40, method="nearest")['wdir'].values

        with open('{}_FORCING_wind.csv'.format(i), "w") as f:

            f.write("{}\n".format(wind_val))

        with open('{}_FORCING_dir.csv'.format(i), "w") as f:

            f.write("{}\n".format(wind_dir))




def write_run_file():

    all_times = ['f{:03}'.format(i) for i in range(1,24,1)]

    for j in all_times :

        direction = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_dirpw.csv'.format(todaysdate,j), delimiter=',')

        period = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_perpw.csv'.format(todaysdate,j), delimiter=',')

        wave_height = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_swh.csv'.format(todaysdate,j), delimiter=',')

        wind_speed = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_wind.csv'.format(todaysdate,j), delimiter=',')

        wind_direction = np.loadtxt('{}/gfswave.t00z.global.0p16.{}.grib2_FORCING_dir.csv'.format(todaysdate,j), delimiter=',')



        print (j)

        f = open("{}/{}.swn".format(todaysdate,j), "w")

        f.write('$****************LAAMU {} {} ****************************************'.format(todaysdate, j))

        f.write('\n')
        f.write('\n')

        f.write('PROJ \'LAAMU_{}\' \'{}\''.format(todaysdate, j))

        f.write('\n')

        f.write('\n')

        f.write('SET depmin 0.0 NAUTICAL')

        f.write('\n')
        f.write('\n')

        f.write('$CGRID 295668.0 191709.0 0. 55000.00 52000.00 100 100 CIRCLE 36 0.0521 1. 31')

        f.write('\n')

        f.write('CGRID UNSTRUCTURED CIRCLE 36 0.0521 1. 31')
        f.write('\n')
        f.write('\n')

        f.write('READ UNSTRUCTURED triangle \'../INITIALISATION/MESH_BATHY/TEST.4\'')

        f.write('\n')
        f.write('\n')

        f.write('INPgrid BOTtom REGular 295668.0 191709.0 0. 999 999 55. 55. EXCeption 999999.00')
        f.write('\n')
        f.write('READinp BOTtom -1. \'../INITIALISATION/MESH_BATHY/clippedbathy_1000_1000.csv\' 4 FREE')

        f.write('\n')
        f.write('\n')

        f.write('BOUN SHAPE JON 3.3 PEAK DSPR DEGREES')
        f.write('\n')
        f.write('BOUN SIDE 101 CONST PAR {} {} {} 30'.format(wave_height[0],period[0],direction[0]))
        f.write('\n')
        f.write('BOUN SIDE 102 CONST PAR {} {} {} 30'.format(wave_height[1],period[1],direction[1]))
        f.write('\n')
        f.write('BOUN SIDE 103 CONST PAR {} {} {} 30'.format(wave_height[2],period[2],direction[2]))
        f.write('\n')
        f.write('BOUN SIDE 104 CONST PAR {} {} {} 30'.format(wave_height[3],period[3],direction[3]))

        f.write('\n')
        f.write('\n')

        f.write('WIND {} {}'.format(wind_speed,wind_direction))
        f.write('\n')
        f.write('\n')

        f.write('GEN3 JANSSEN 4.5 0.5 AGROW 0.003')
        f.write('\n')
        f.write('QUAD')
        f.write('\n')
        f.write('BREA')
        f.write('\n')
        f.write('WCAP')
        f.write('\n')
        f.write('\n')
        f.write('$********************* OUTPUT REQUESTS *************************')
        f.write('\n')
        f.write('\n')
        f.write('BLOCK  \'COMPGRID\' NOHEAD \'Laamu_{}_{}.vtu\' LAYOUT 3 XP YP BOTLEV WATLEV DEPTH HS TM01 DSPR PDIR VEL FRCOEFF TPS URMS'.format(todaysdate,j))
        f.write('\n')
        f.write('TEST 1,0')
        f.write('\n')
        f.write('COMPUTE')
        f.write('\n')
        f.write('STOP')

        f.close()


def run_files():

    all_swan_files = ['f{:03}.swn'.format(i) for i in range(1,24,1)]

    with open('{}/run_all.sh'.format(todaysdate), 'w') as r:

        for k in all_swan_files:

            r.write('swanrun -input {}'.format(k))

            r.write('\n')

    os.chdir('{}'.format(todaysdate))

    subprocess.call('./run_all.sh', shell=True)


def run_files_powershell():

    all_swan_files = ['f{:03}.swn'.format(i) for i in range(1,24,1)]

    with open('{}/run_all.ps1'.format(todaysdate), 'w') as r:

        for k in all_swan_files:

            r.write('swanrun {} 12'.format(k)[:12])

            r.write('\n')

    os.chdir('{}'.format(todaysdate))

    subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "run_all.ps1"])




#schedule.every(1).seconds.do(write_run_file)

#schedule.every(1).seconds.do(run_files)

#schedule.every(1).seconds.do(get_gfs_grib)

#schedule.every(1).seconds.do(get_bund_valss)

#schedule.every(1).seconds.do(get_winds)

#schedule.every(1).seconds.do(write_run_file)

#schedule.every(1).seconds.do(run_files)

#schedule.every(1).seconds.do(run_files_powershell)




'''
schedule.every().day.at('21:00').do(get_gfs_grib)

schedule.every().day.at('21:05').do(get_bund_valss)

schedule.every().day.at('21:10').do(write_run_file)

schedule.every().day.at('21:15').do(run_files)


'''

while True:
    schedule.run_pending()
    time.sleep(1)

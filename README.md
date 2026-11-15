# Waktu Solat
Waktu Solat is a desktop application developed with Python PyQt6 library to provide accurate Malaysia and Australia praying times.
## Background
Waktu Solat was once a sandbox file to learn and experiment with PyQt6 features and API usages within Python. It was mainly used alongside Qt designer in designing UI placements and parameters. Over time, new functionalites are added in conjunction with my leaning input to become the current file.

## Features

- Daily prayer time updates.
- Customizable location in Malaysia and Australia
- Notification for when it is time for prayer
- Runs in system tray background.  

## Prayer Time Calculation

|                               |           **Malaysia**          |    **Australia**    |
|-------------------------------|:-------------------------------:|:-------------------:|
| Organization                  | Jabatan Kemajuan Islam Malaysia | Muslim World League |
| Fajr Sun Angle under Horizon  | 19.5 degrees                    | 18 degrees          |
| Isha Sun Angle under Horizon  | 17.5 degrees                    | 17 degrees          |
| Shafaq                        | Ahmar                           | Ahmar               |

## Usage

Download ```.exe``` here -> [LanxWaktuSolat.exe](https://1drv.ms/u/c/429aeee96853109f/IQAmT4c5c9pbQptcvmvrWeftARgSAlVXze0pRrYLP3x5QHw?e=WjDdGR)

or

Git pull this repository.
Run ```pip install -r requirements.txt``` to install the required libraries.<br>
Then, run ```solat.py```.<br><br>
Currently, Waktu Solat serves a basic purpose of showing prayer time for the day with simple UI designs.<br><br>
![image](https://github.com/user-attachments/assets/49e526b3-33cb-41b1-b4cc-79ec45e3d7bc)


## Future
- Azan settings
- Notification settings
- Better UI perhaps.
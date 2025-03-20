import os
import shutil
import glob
from datetime import datetime


def load_setting():
    """
    Assemble your linearization possiblilities:

    setting[0] => Complex power constraint
                0 Conic
                1 Lin with equal length blocks
                2 Lin with log lenght block

    setting[1] => Number of block for power linearization

    setting[2] => Type of Substation limits
                0 Conic
                1 Linearized ext (mult = scale_factor)
                2 Linearized int (mult = 1)

    setting[3] => Number of segments for linearization
    """

    lin_test = {}
    lin_test[0] = [2,15,2,16] 
    
    

    string = 'Irradiation_fixed_800_w_exp_'
    folder_name = string + datetime.now().strftime("%d%m-%H%M")

    return lin_test, folder_name


def move_files_to_folder(folder_name='organized_files'):
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Find all .png and .csv files in the current directory
    png_files = glob.glob('*.png')
    csv_files = glob.glob('*.csv')
    txt_files = glob.glob('*.txt')
    log_files = glob.glob('*.log')
    lp_files = glob.glob('*.lp')
    pkl_files = glob.glob('*.pkl')
    
    # Move .png files to the new folder
    for file in png_files:
        shutil.move(file, os.path.join(folder_name, file))
    
    # Move .csv files to the new folder
    for file in csv_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .txt files to the new folder
    for file in txt_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .log files to the new folder
    for file in log_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .lp files to the new folder
    for file in lp_files:
        shutil.move(file, os.path.join(folder_name, file))

    # Move .pkl files to the new folder
    for file in pkl_files:
        shutil.move(file, os.path.join(folder_name, file))
    
    print(f"Moved files to '{folder_name}'.")

# Call the function at the end of your script


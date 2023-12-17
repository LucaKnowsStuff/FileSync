"""
Author:José Luca Baptista Pereira
Email:lucajk15@gmail.com
GitHub: https://github.com/LucaKnowsStuff
Linkdin: https://www.linkedin.com/in/luca-pereira-769866267/
"""


import os 
import hashlib
import shutil
import argparse
import time 
import logging

# Function to calculate the hash of a file using md5 algorithm
def calculate_file_md5(chunk_size : int , file_path : str): 
    md5 = hashlib.md5()
     #We use the file name in the hashing process to be able to diferciate files that may have the same content
    file_name = os.path.basename(file_path)
    md5.update(file_name.encode('utf-8')) 
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def compare_dir(source : str, replica : str ):
    #List of files that need to be deleted from the replica folder 
    files_to_delete = []
    #List of files that need to be copies from the source folder to the replica
    files_to_copy = []
    #List of directories that need to bo deleted in the replica folder
    dirs_to_delete = []
    #Dictionary that stores the paths of the files in the source folder as keys and theyr hashes as values
    hash_source = {}
    #List of all the directories in the source folder that need to exist in the replica aswell
    protected_dirs = [] 
    #Control variable to tell if the for loop is running for the first time or not (used to prevent the replica directory of bing stored in the dirs_to_delete list)
    first_run = True
    #Go trhough all the directories and files in the source folder
    for dirpath , dirnames , filenames in os.walk(source):
        #Store the current directory 
        protected_dirs.append(dirpath)
        #Go though all the files in the current directory
        for filename in filenames:
            #Get the path of the file
            file_path = os.path.join(dirpath, filename)
            #Get its relative path in realtion to the source folder
            file_path_rel = os.path.relpath(file_path , source)
            #Store the path and the hash of the file
            hash_source[file_path_rel] = calculate_file_md5(4096 ,file_path)
            #All files in the source folder are added to the copy list initialy
            files_to_copy.append(file_path)    
    #Go trhough all the directories in the replica folder
    for dirpath , dirnames , filenames in os.walk(replica):
        #Create a hipothetical path of the current directory (if this direcotry exists in the source fodler it will have this path)
        replica_dir = os.path.join(source , os.path.relpath(dirpath , replica))
        #Add all directories that are in the replcia folder but not in the source to the list of directories that are to be deleted
        if first_run == False and replica_dir not in protected_dirs:
            dirs_to_delete.append(dirpath)
        #Go trhough all the files in the cuurent directory
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_path_rel = os.path.relpath(file_path ,  replica)
            #Check if the current files path exists in the source folder //Mudar iisto if statment a mais
            if file_path_rel in hash_source.keys():
                hash_s = hash_source[file_path_rel]
                hash_r = calculate_file_md5(4096 , file_path)
                #Check if the contents of the files are the same , if they arent the file needs to be deleted
                if hash_s != hash_r:
                    files_to_delete.append(file_path)
                #If the contents are the same then the file is up to date and can be reomved from the copy list
                else:
                    files_to_copy.remove(os.path.join(source, file_path_rel))
            #If the fiels doesn´t even have the same path it needs to be deleted
            else:
                files_to_delete.append(file_path)
        first_run = False
    
    protected_dirs.pop(0)

   
    return files_to_copy , files_to_delete , dirs_to_delete , protected_dirs

#Funtion takes a list of paths to files and a list of paths to direcotries and deletes them if they exist
def delete_files_and_dirs(files_to_delete : list , dirs_to_delete : list):
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            logging.info(f"[Delete File] File {file_path} has been deleted")
        except OSError as e:
            logging.error(f"[DELETE ERROR] File {file_path} could not be deleted. Error: {e}")
            print(f"Error deleteing the file: {file_path} : {e}")
    for dir_path in dirs_to_delete:
        try:
            shutil.rmtree(dir_path)
            logging.info(f"[Delete Folder] Folder {dir_path} has been deleted")
        except OSError as e:
            print(f"Error deleteing the directory: {dir_path} : {e}")
            logging.error(f"[DELETE ERROR] Folder {dir_path} could not be deleted. Error: {e}")

#Function takes a list of paths to files and a list of paths to directories and copies them from a source to a replica folder 
def copy_files(files_to_copy : list, protected_dirs : list ,source : str, replica : str ):
    #Create all directories in the source folder in the replica if they dont exist
    for dir in protected_dirs:
        rel_path = os.path.relpath(dir , source)
        dir_path = os.path.join(replica , rel_path)
        os.makedirs(dir_path, exist_ok=True) 
    try:    
        #Copies all the files in the copy list to the replica folder
        for file_path in files_to_copy:
            rel_path = os.path.relpath(file_path, source )          
            destination_path = os.path.join(replica, rel_path) 
            shutil.copy2(file_path, destination_path)
            logging.info(f"[File Copied] File {file_path} copied from Source to {destination_path}")
    except FileNotFoundError:
        print(f"Copying failed , the file: {file_path} ,  doesn´t exist!")
        logging.error(f"[COPY ERROR] File {file_path} could not be found")
    except Exception as e:
        print(f"Error when copying the file: {file_path} : {e}")
        logging.error(f"[COPY ERROR] File {file_path} could not be copied. Error: {e}")

#Function that checks if a file or directory exists  exists
def check_dir_exists(dir):
    path = os.path.abspath(dir)
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"The file or directory '{dir}' doesn´t exist!")
    return dir

#Funtion that handles the users command line input 
def handle_arguments():
    try:    
        parser = argparse.ArgumentParser()
        parser.add_argument('original_folder_path' , type=check_dir_exists , help="Path to the original folder")
        parser.add_argument('replica_folder_path' , type=check_dir_exists , help="Path to the replica folder")
        parser.add_argument('log_file' , type=check_dir_exists ,help="Path to the log file" )
        parser.add_argument("-t ", "--time" , type= int , default= 15 ,help="Time interval in seconds between syncronization cycles (15s default)")
        args = parser.parse_args()
        return args
    except argparse.ArgumentTypeError as e:
        print(f"Argument error: {e}")
        exit(1)


#Main function that dictates the flow of the program 
def main():
    args = handle_arguments()
    logging.basicConfig(filename=args.log_file , level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    original_folder = args.original_folder_path
    replica_folder = args.replica_folder_path
    print("Press Ctrl + C to close the program")
    
    while True:
        try:   
            files_to_copy , files_to_delete , dirs_to_delete , protected_dirs = compare_dir(original_folder , replica_folder)
            delete_files_and_dirs(files_to_delete , dirs_to_delete)
            copy_files(files_to_copy ,protected_dirs , original_folder , replica_folder)
            print("Cycle Completed with success!")
            logging.info(f"[CYCLE FINISHED]Syncing cycle completed. N. of files copied: {len(files_to_copy)} N. of files deleted: {len(files_to_delete)}")
            time.sleep(args.time)
        except KeyboardInterrupt:
            print("Program closed by user")
            exit(0)

if __name__ == '__main__':
    main()
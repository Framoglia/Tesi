from datetime import datetime  # Correct import

# Check if the import works correctly
print(datetime)  # This should print something like <class 'datetime.datetime'>

folder_name = "your_folder_name" + datetime.now().strftime("%d%m-%H%M")
print(folder_name)

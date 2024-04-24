import pandas as pd
from PIL import Image
import os
import numpy as np

# Function to rotate an image by a specified angle
"""def rotate_image(image, angle):
    return image.rotate(angle, expand=True)

# Read the original CSV file
original_csv_folder = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\'
original_csv_file = original_csv_folder + 'dice - data-2.csv'
augmented_csv_file = original_csv_folder + 'dice - data-2-augmented.csv'

#original_csv_file = 'original_data.csv'  # Update with the actual path to your original CSV file
data = pd.read_csv(original_csv_file)

# Create a list to store augmented data
augmented_data = []
original_images_folder = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice\\'
augmented_images_folder_out = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice2\\'
# Augment each image in the original data
for index, row in data.iterrows():
    filename = row['filename']
    label = row['label']

    # Load the original image
    image_path = os.path.join(original_images_folder, filename)  # Update with the folder containing your original images
    original_image = Image.open(image_path)
    num_of_images = 20
    # Rotate the image by 360/12 degrees (30 degrees)
    for i in range(num_of_images):
        angle = i * (360 / num_of_images)
        rotated_image = rotate_image(original_image, angle)

        # Save the rotated image with a new filename
        new_filename = f'{filename[:-4]}_rotated_{i}.jpg'
        rotated_image.save(os.path.join(augmented_images_folder_out, new_filename))  # Update with the folder to save augmented images

        # Append the filename and label to the augmented data list
        augmented_data.append({'filename': new_filename, 'label': label})

# Convert augmented data to DataFrame
augmented_df = pd.DataFrame(augmented_data)

# Concatenate original data with augmented data
all_data = pd.concat([data, augmented_df], ignore_index=True)

# Write all data to a new CSV file
output_csv_file = augmented_csv_file  # Update with the desired path for the augmented CSV file
all_data.to_csv(output_csv_file, index=False)
"""


import pandas as pd
from PIL import Image
import os
import numpy as np

"""# Function to rotate an image by a specified angle and crop to the center
def rotate_and_crop_image(image, angle, output_size):
    # Rotate the image
    rotated_image = image.rotate(angle, expand=True)

    # Crop the image to the center
    width, height = rotated_image.size
    left = (width - output_size[0]) / 2
    top = (height - output_size[1]) / 2
    right = (width + output_size[0]) / 2
    bottom = (height + output_size[1]) / 2
    cropped_image = rotated_image.crop((left, top, right, bottom))

    return cropped_image

# Path to the original CSV folder
original_csv_folder = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\'  # Update with the path to your original CSV folder

original_images_folder = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice\\'
augmented_images_folder_out = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\dice2\\'

# Read the original CSV file
original_csv_file = os.path.join(original_csv_folder, 'dice_data.csv')  
data = pd.read_csv(original_csv_file)

# Create a list to store augmented data
augmented_data = []

# Output image size
output_size = (200, 200)

# Augment each image in the original data
for index, row in data.iterrows():
    filename = row['filename']
    label = row['label']

    # Load the original image
    image_path = os.path.join(original_csv_folder, "dice\\" ,filename)  # Update with the folder containing your original images
    original_image = Image.open(image_path)

    # Rotate the image by 360/12 degrees (30 degrees)
    for i in range(20):
        angle = i * (360 / 20)
        rotated_image = rotate_and_crop_image(original_image, angle, output_size)

        # Save the rotated image with a new filename
        new_filename = f'{filename[:-4]}_rotated_{i}.jpg'
        rotated_image.save(os.path.join(augmented_images_folder_out, new_filename))  # Update with the folder to save augmented images

        # Append the filename and label to the augmented data list
        augmented_data.append({'filename': new_filename, 'label': label})

# Convert augmented data to DataFrame
augmented_df = pd.DataFrame(augmented_data)

# Concatenate original data with augmented data
all_data = pd.concat([data, augmented_df], ignore_index=True)

# Write all data to a new CSV file
output_csv_file = os.path.join(original_csv_folder, 'augmented_data-new.csv')  # Update with the desired path for the augmented CSV file
all_data.to_csv(output_csv_file, index=False)"""




def scramble_excel(input_excel, output_excel):
    # Read the input Excel file
    data = pd.read_csv(input_excel)
    
    # Shuffle the rows randomly
    shuffled_data = data.sample(frac=1).reset_index(drop=True)
    
    # Write shuffled data to a new Excel file
    shuffled_data.to_csv(output_excel, index=False)

# Example usage:
    
original_csv_folder = 'C:\\Users\\alonb\\OneDrive\\arduino\\backgammon\\dice data\\'
augmented_csv_file = 'C:\\temp\\augmented_data-new.csv'
scrambled_augmented_csv_file = 'c:\\temp\\dice-augmented-new-scrambled.csv'
#input_excel_file = r'C:\path\to\input_excel.xlsx'  # Update with the path to your input Excel file
#output_excel_file = r'C:\path\to\output_excel.xlsx'  # Update with the desired path for the output Excel file

scramble_excel(augmented_csv_file, scrambled_augmented_csv_file)
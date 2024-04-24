import pandas as pd
import os
import cv2

def update_excel_file(file_path, search_string, number1, number2):
    try:
        # Check if the Excel file exists
        if not os.path.exists(file_path):
            # If the file doesn't exist, create a new DataFrame with columns
            df = pd.DataFrame(columns=['Image', 'Dice1', 'Dice2'])
        else:
            # If the file exists, load it into a DataFrame
            df = pd.read_excel(file_path)

        # Check if the search string is already in the DataFrame
        if search_string in df['Image'].values:
            # Update the numbers if the string is found
            df.loc[df['Image'] == search_string, 'Dice1'] = number1
            df.loc[df['Image'] == search_string, 'Dice2'] = number2
        else:
            # Add a new row if the string is not found
            new_row = {'Image': search_string, 'Dice1': number1, 'Dice2': number2}
            # Use concat to concatenate the new row to the DataFrame
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        # Save the updated DataFrame back to the Excel file
        df.to_excel(file_path, index=False)

        print(f"{search_string} - Excel file updated successfully.")

    except Exception as e:
        print(f"Error updating Excel file: {e}")

def display_image_info(image, existing_text, count_text,current_image_path):
    # Display existing numbers and count on the image
    cv2.putText(image, existing_text, (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(image, current_image_path, (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    #cv2.putText(image, count_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

def browse_images_with_auto_update(folder_path,move_to = ""):
    try:
        # Get a list of all image files in the folder
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

        if not image_files:
            print("No image files found in the folder.")
            return

        # Initialize index to point to the first image
        current_index = 0
        loop_started = False
        while True:
            # Open the current image using OpenCV
            current_image_path = os.path.join(folder_path, image_files[current_index])
            if loop_started == True or move_to == "" or (image_files[current_index] == move_to):
                loop_started = True
                image = cv2.imread(current_image_path)
                # Display the count of images mentioned in Excel out of total images
                if os.path.exists("C:\\temp\\dice_test_list.xlsx"):
                    df = pd.read_excel("C:\\temp\\dice_test_list.xlsx")
                    mentioned_images_count = df.shape[0]
                    total_images_count = len(image_files)
                    count_text = f"Images in Excel: {mentioned_images_count}/{total_images_count}"
                    display_image_info(image, "", count_text,current_image_path)

                # Check if the image filename is in the Excel file
                if os.path.exists("C:\\temp\\dice_test_list.xlsx"):
                    df = pd.read_excel("C:\\temp\\dice_test_list.xlsx")
                    if image_files[current_index] in df['Image'].values:
                        # Display existing numbers on the image
                        existing_numbers = df.loc[df['Image'] == image_files[current_index], ['Dice1', 'Dice2']]
                        existing_text = f"Ex: {existing_numbers.values.flatten()}"
                        # Display the count along with existing numbers
                        display_image_info(image, existing_text, count_text,current_image_path)

                # Display the image
                cv2.imshow('Image', image)

                # Prompt user for next action
                key = cv2.waitKey(0) & 0xFF

                # Handle user input
                if key == ord('p'):
                    current_index = (current_index + 1) % len(image_files)
                elif key == ord('o'):
                    current_index = (current_index - 1) % len(image_files)
                elif chr(key).isdigit():
                    # If a digit is pressed, wait for the second digit
                    first_digit = int(chr(key))
                    second_digit = cv2.waitKey(0) & 0xFF
                    
                    if chr(second_digit).isdigit():
                        # Combine the two digits and call update_excel_file
                        digits_input = int(str(first_digit) + chr(second_digit))
                        update_excel_file("C:\\temp\\dice_list.xlsx", image_files[current_index], digits_input // 10, digits_input % 10)

                    # Automatically move to the next image
                    current_index = (current_index + 1) % len(image_files)
            else:
                current_index = (current_index + 1) % len(image_files)
        # Close the OpenCV window after exiting the loop
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error browsing images: {e}")

# Example usage:
folder_path = 'C:\\dice_test\\'
browse_images_with_auto_update(folder_path,"")


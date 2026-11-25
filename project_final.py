import tkinter as tk
from tkinter import Label, ttk
from tkinter import messagebox
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text  
from PIL import Image, ImageTk
from tkinter import font as tkFont
from tkinter import Toplevel, Label, Entry, Button


# Global DataFrame to hold crop data
df = pd.DataFrame()

def connect_to_db():
    connection_string = "mysql+mysqlconnector://user:sql123@localhost/farmer"
    engine = create_engine(connection_string)
    return engine

def fetch_data(engine):
    query = "SELECT crop_name AS crop, soiltype, description, irrig, season FROM crop"  # Ensure 'season' is included in the query
    df = pd.read_sql_query(query, engine)
    return df

def fetch_details(engine):
    query = "SELECT details FROM about"  # Fetching details from the about table
    about_df = pd.read_sql_query(query, engine)
    return about_df

def fetch_credits(conn):
    query = "SELECT writeup FROM credits"  # Adjust the query as needed
    return pd.read_sql(query, conn)  # Assuming you're using pandas to read SQL

def show_description(crop_name):
    crop_info = df[df['crop'] == crop_name].iloc[0]
    description = crop_info['description']
    messagebox.showinfo("Crop Description", description)

def apply_filters():
    # Apply the selected filters to the DataFrame
    filtered_df = df.copy()

    # Filter by soil type
    selected_soil_types = [soil_type for soil_type, var in soil_vars.items() if var.get()]
    if selected_soil_types:
        filtered_df = filtered_df[filtered_df['soiltype'].isin(selected_soil_types)]

    # Filter by irrigation type
    selected_irrigation_types = [irrigation_type for irrigation_type, var in irrigation_vars.items() if var.get()]
    if selected_irrigation_types:
        filtered_df = filtered_df[filtered_df['irrig'].isin(selected_irrigation_types)]

    # Filter by crop type
    selected_crop_types = [crop_type for crop_type, var in crop_type_vars.items() if var.get()]
    if selected_crop_types:
        filtered_df = filtered_df[filtered_df['season'].isin(selected_crop_types)]

    return filtered_df

def reload_tiles(canvas, no_results_label):
    # Apply filters
    filtered_df = apply_filters()

    # Clear existing tiles
    for widget in canvas.winfo_children():
        widget.destroy()

    # Create new tiles with filtered data
    tiles = []
    tile_width = 800  # Set a larger fixed width for the tiles
    tile_height = 200  # Set a base height for each tile
    padding = 20  # Uniform space between tiles

    for index, row in filtered_df.iterrows():
        name = row['crop']
        soil_type = row['soiltype']
        irrigation_type = row['irrig']
        season = row['season']  # Get the season type
        description = row['description']

        # Create a frame for the tile to hold the label and button
        tile_frame = tk.Frame(canvas, bg="#444444", relief=tk.RAISED, bd=2, width=tile_width, height=tile_height)  # Set width and height

        # Set the crop name as the heading
        heading_label = tk.Label(tile_frame, text=name, font=("Arial", 16, "bold"), bg="#444444", fg="#ffffff")
        heading_label.pack(pady=(5, 2))

        # Display additional details in the tile
        details_label = tk.Label(tile_frame, text=f"Soil Type: {soil_type}\nIrrigation Requirements: {irrigation_type}\nType: {season}", 
                                 bg="#444444", fg="#ffffff")
        details_label.pack(padx=5, pady=(0, 5))

        # Create a label for the description with wraplength
        description_label = tk.Label(tile_frame, text=description, bg="#444444", fg="#ffffff", wraplength=tile_width - 20)  # Adjust wraplength based on width
        description_label.pack(padx=5, pady=(0, 5))

        # Create the Select button
        select_button = tk.Button(tile_frame, text="Select", 
                                  command=lambda name=name, soil=soil_type, irrig=irrigation_type, season=season, desc=description: select_crop(name, soil, irrig, season, desc), 
                                  bg="#1DB954", fg="#ffffff")
        select_button.pack(side=tk.BOTTOM, anchor='se', padx=5, pady=5)

        # Bind the heading label to show the description
        heading_label.bind("<Button-1>", lambda event, name=name: show_description(name))

        # Add the tile frame to the list
        tiles.append(tile_frame)

    if len(tiles) == 0:
        no_results_label.place(relx=0.5, rely=0.5, anchor='center')  # Display the label when there are no results
    else:
        # Center the tiles
        for index, tile in enumerate(tiles):
            tile.update_idletasks()  # Update the tile to get its correct width
            center_x = (canvas.winfo_width() - tile_width) // 2  # Calculate center x position
            canvas.create_window(center_x, 20 + index * (tile_height + padding), anchor='nw', window=tile)  # Position the tile

        # Update the scroll region of the canvas
        canvas.configure(scrollregion=canvas.bbox("all"))

        # Scroll to the top after reloading
        canvas.yview_moveto(0)  # Ensure the scrollbar starts at the top
        no_results_label.place_forget()  # Hide the label when there are results

def select_crop(crop_name, soil_type, irrigation_type, season, description):
    print(f"Attempting to select crop: {crop_name}")  # Debugging output
    conn = connect_to_db()
    try:
        with conn.connect() as connection:
            print("Database connection successful.")  # Debugging output
            
            # Check if the crop already exists in the report
            check_query = text("SELECT COUNT(*) FROM report WHERE crop = :crop_name")
            result = connection.execute(check_query, {'crop_name': crop_name}).scalar()
            
            if result > 0:
                messagebox.showwarning("Duplicate Entry", f"The crop '{crop_name}' already exists in the report.")
                return
            
            # Fetch steps for the selected crop from the database
            steps_query = text("SELECT steps FROM crop WHERE crop_name = :crop_name")
            steps_result = connection.execute(steps_query, {'crop_name': crop_name}).fetchone()
            
            # Access steps using index if steps_result is a tuple
            steps = steps_result[0] if steps_result else None  # Get steps or None if not found
            
            insert_query = text("""
            INSERT INTO report (crop, soiltype, description, irrig, season, steps)
            VALUES (:crop_name, :soil_type, :description, :irrigation_type, :season, :steps)
            """)
            print(f"Inserting crop: {crop_name}, soil type: {soil_type}, irrigation: {irrigation_type}, season: {season}, description: {description}, steps: {steps}")  # Debugging output
            connection.execute(insert_query, {
                'crop_name': crop_name,
                'soil_type': soil_type,
                'description': description,
                'irrigation_type': irrigation_type,
                'season': season,
                'steps': steps
            })
            connection.commit()  # Commit the transaction
            messagebox.showinfo("Crop Selected", f"You have selected: {crop_name}")

    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")
        print(f"Error inserting data: {str(e)}")  # Debugging output

def cropfilter_page():
    clear_frame()  # Clear the current frame
    cropfilter_frame = tk.Frame(main_frame, bg="#333333")
    cropfilter_frame.pack(fill=tk.BOTH, expand=True)

    # Create a frame for the header (to hold the title)
    header_frame = tk.Frame(cropfilter_frame, bg="#333333")
    header_frame.pack(fill=tk.X)  # Fill the width of the crop filter frame

    # Create a center frame to hold the title label
    center_frame = tk.Frame(header_frame, bg="#333333")
    center_frame.pack(side=tk.TOP, expand=True)  # Allow the center frame to expand

    # Add the title label to the center frame
    title_label = tk.Label(center_frame, text="Crop Filter", font=tkFont.Font(family="Georgia", size=50, weight="bold", underline=True), bg="#333333", fg="#00FF00")
    title_label.pack(pady=10)  # Place at the top with vertical padding

    # Create a canvas for scrolling
    canvas = tk.Canvas(cropfilter_frame, bg="#333333")
    scrollable_frame = tk.Frame(canvas, bg="#333333")

    # Create a vertical scrollbar
    scrollbar = ttk.Scrollbar(cropfilter_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas to work with the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a window in the canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")  # Anchor to the north-west

    # Update the scroll region of the canvas
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_configure)

    # Connect to the database and fetch data
    global df
    conn = connect_to_db()
    df = fetch_data(conn)

    # Create filters on the right side
    filter_frame = tk.Frame(cropfilter_frame, bg="#333333", width=200)
    filter_frame.pack(side=tk.RIGHT, fill=tk.Y)

    # Get unique soil types
    soil_types = df['soiltype'].unique().tolist()

    # Add "Soil Type" label
    soil_type_label = tk.Label(filter_frame, text="Soil Type", font=("Helvetica", 12), bg="#333333", fg="#ffffff")
    soil_type_label.pack(pady=10)

    # Checkboxes for each soil type
    global soil_vars
    soil_vars = {soil_type: tk.BooleanVar(value=True) for soil_type in soil_types}
    soil_checkboxes = [tk.Checkbutton(filter_frame, text=soil_type, variable=soil_vars[soil_type], bg="#333333", fg="#ffffff", selectcolor="#555555") for soil_type in soil_types]
    for checkbox in soil_checkboxes:
        checkbox.pack(anchor='w')

    # Add space between criteria
    tk.Label(filter_frame, text="", bg="#333333").pack()

    # Add "Irrigation" label
    irrigation_label = tk.Label(filter_frame, text="Irrigation", font=("Helvetica", 12), bg="#333333", fg="#ffffff")
    irrigation_label.pack(pady=10)

    # Get unique irrigation types
    irrigation_types = df['irrig'].unique().tolist()

    # Checkboxes for each irrigation type
    global irrigation_vars
    irrigation_vars = {irrigation_type: tk.BooleanVar(value=True) for irrigation_type in irrigation_types}
    irrigation_checkboxes = [tk.Checkbutton(filter_frame, text=irrigation_type, variable=irrigation_vars[irrigation_type], bg="#333333", fg="#ffffff", selectcolor="#555555") for irrigation_type in irrigation_types]
    for checkbox in irrigation_checkboxes:
        checkbox.pack(anchor='w')

    # Add space between criteria
    tk.Label(filter_frame, text="", bg="#333333").pack()

    # Add "Type" label
    type_label = tk.Label(filter_frame, text="Type", font=("Helvetica", 12), bg="#333333", fg="#ffffff")
    type_label.pack(pady=10)

    # Define crop type options
    crop_type_options = ['Kharif', 'Rabi', 'Zaid']
    global crop_type_vars
    crop_type_vars = {crop_type: tk.BooleanVar(value=True) for crop_type in crop_type_options}

    # Create checkboxes for each crop type
    crop_type_checkboxes = [tk.Checkbutton(filter_frame, text=crop_type, variable=crop_type_vars[crop_type], bg="#333333", fg="#ffffff", selectcolor="#555555") for crop_type in crop_type_options]
    for checkbox in crop_type_checkboxes:
        checkbox.pack(anchor='w')

    # Add space between criteria and reload button
    tk.Label(filter_frame, text="", bg="#333333").pack()

    # Reload button
    reload_button = tk.Button(filter_frame, text="Reload", command=lambda: reload_tiles(canvas, no_results_label), bg="#333333", fg="white")    
    reload_button.pack(pady=10)

    # Label to display "No Results" message
    no_results_label = tk.Label(cropfilter_frame, text="No Results", font=("Helvetica", 20), fg="red", bg="#333333")
    no_results_label.place(relx=0.5, rely=0.5, anchor='center')
    no_results_label.pack_forget()  # Initially, hide the label

    # Initial load of tiles
    reload_tiles(canvas, no_results_label)  # Update the scroll region of the canvas
    scrollable_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

def clear_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()

def change_password(username, old_password, new_password):
    conn = connect_to_db()  # Connect to the database
    try:
        with conn.connect() as connection:
            # Check if the old password is correct
            check_query = text("SELECT password FROM account WHERE username = :username")

            print(f"Executing: {check_query}, with parameters: {{'username': '{username}'}}")
            
            result = connection.execute(check_query, {'username': username}).scalar()

            if result is None:
                messagebox.showerror("Error", "Username not found.")
                return
            
            if result != old_password:
                messagebox.showerror("Error", "Old password is incorrect.")
                return
            
            # Update the password
            update_query = text("UPDATE account SET password = :new_password WHERE username = :username")
            print(f"Executing: {update_query}, with parameters: {{'username': '{username}', 'new_password': '{new_password}'}}")
            connection.execute(update_query, {'username': username, 'new_password': new_password})

            # Commit the changes
            connection.commit()  # Ensure changes are committed

            # Verify the update
            verify_query = text("SELECT password FROM account WHERE username = :username")
            updated_password = connection.execute(verify_query, {'username': username}).scalar()
            print(f"Updated password for {username}: {updated_password}")

            messagebox.showinfo("Success", "Password changed successfully.")

    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")
        print(f"Error changing password: {str(e)}")  # Debugging output

BACKGROUND_COLOR = "#f0f0f0"  # Example: light gray
BUTTON_COLOR = "#d9d9d9"  # Example: light button color

def open_change_password_dialog():
    # Create a new Toplevel window
    dialog = tk.Toplevel(root)
    dialog.title("Change Password")
    dialog.geometry("700x600")  # Set the size of the dialog

    # Set the background color of the dialog
    dialog.configure(bg="#333333")  # Match the main frame background color

    # Set a consistent padding for the dialog
    padding = 10

    # Create a frame to hold the content and center it
    content_frame = tk.Frame(dialog, bg="#333333")
    content_frame.place(relx=0.5, rely=0.5, anchor='center')  # Center the frame in the dialog

    # Username Label and Entry
    username_label = tk.Label(content_frame, text="Username:", bg="#333333", fg="#FFFFFF", font=tkFont.Font(family="Georgia", size=14))
    username_label.grid(row=0, column=0, padx=padding, pady=padding, sticky='w')
    username_entry = tk.Entry(content_frame, font=tkFont.Font(family="Georgia", size=14))
    username_entry.grid(row=0, column=1, padx=padding, pady=padding)

    # Old Password Label and Entry
    old_password_label = tk.Label(content_frame, text="Old Password:", bg="#333333", fg="#FFFFFF", font=tkFont.Font(family="Georgia", size=14))
    old_password_label.grid(row=1, column=0, padx=padding, pady=padding, sticky='w')
    old_password_entry = tk.Entry(content_frame, show="*", font=tkFont.Font(family="Georgia", size=14))
    old_password_entry.grid(row=1, column=1, padx=padding, pady=padding)

    # New Password Label and Entry
    new_password_label = tk.Label(content_frame, text="New Password:", bg="#333333", fg="#FFFFFF", font=tkFont.Font(family="Georgia", size=14))
    new_password_label.grid(row=2, column=0, padx=padding, pady=padding, sticky='w')
    new_password_entry = tk.Entry(content_frame, show="*", font=tkFont.Font(family="Georgia", size=14))
    new_password_entry.grid(row=2, column=1, padx=padding, pady=padding)

    # Change Password Button
    change_password_button = tk.Button(content_frame, text="Change Password", bg="#00FF00",  # Match button color
                                        command=lambda: change_password(username_entry.get(), old_password_entry.get(), new_password_entry.get()),
                                        font=tkFont.Font(family="Georgia", size=14))
    change_password_button.grid(row=3, columnspan=2, pady=padding)

    # Optional: Add a cancel button for better user experience
    cancel_button = tk.Button(content_frame, text="Cancel", bg="#FF0000",  # Red for cancel
                               command=dialog.destroy,
                               font=tkFont.Font(family="Georgia", size=14))
    cancel_button.grid(row=4, columnspan=2, pady=padding)

    # Center the dialog on the screen
    dialog.transient(root)  # Keep the dialog on top of the main window
    dialog.grab_set()  # Make the dialog modal
    root.wait_window(dialog)  # Wait for the dialog to close

def home_page():
    clear_frame()
    home_frame = tk.Frame(main_frame, bg="#333333")
    home_frame.pack(fill=tk.BOTH, expand=True)

    # Update the title label with the new text and font
    title_label = tk.Label(home_frame, text="Welcome to Harvest Hub", 
                           font=tkFont.Font(family="Georgia", size=50, weight="bold"), 
                           bg="#333333", fg="#00FF00")
    title_label.pack(pady=20)

    slogan_label = tk.Label(home_frame, text="All your farming needs, in one place", 
                            font=tkFont.Font(family="Georgia", size=20, slant="italic"),  
                            bg="#333333", fg="#FFFFFF")
    slogan_label.pack(pady=(5, 20))

    # Create a tile for the description
    description_tile = tk.Frame(home_frame, bg="#444444", bd=2, relief="groove", width=600, height=400)
    description_tile.pack(pady=(10, 20), padx=20)

    # Create a vertical scrollbar
    scrollbar = tk.Scrollbar(description_tile)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a Text widget for the description text
    description_text = (
        "Home Page\n"
        "Navigate through the app with ease using buttons to access different sections. "
        "A password change option is available in the top-right corner. The page also includes "
        "a quick guide on how the app works.\n\n"
        "Crop Filter\n"
        "Filter crops based on your needs. Use Reload to refresh the list and Select to transfer "
        "crop-growing details to the next page.\n\n"
        "Report\n"
        "View selected crops with growing instructions. Remove unwanted crops easily using the Delete button.\n\n"
        "About\n"
        "Learn about the app and its purpose, with credits to contributors.\n\n"
        "Click any of the tabs on the side to get started!"
    )

    # Create a Text widget for the description
    description_widget = tk.Text(description_tile, wrap=tk.WORD, bg="#444444", fg="#FFFFFF", font=tkFont.Font(family="Georgia", size=16), bd=0, height=15, width=70, yscrollcommand=scrollbar.set)
    description_widget.insert(tk.END, description_text)  # Insert the text into the Text widget
    description_widget.config(state=tk.NORMAL)  # Make the text widget editable for scrolling
    description_widget.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)  # Fill and expand

    # Configure scrollbar
    scrollbar.config(command=description_widget.yview)  # Link scrollbar to text widget

    # Load the image for the button
    button_image = Image.open("account.jpg") 
    button_image = button_image.resize((50, 50), Image.Resampling.LANCZOS)  # Resize the image if needed
    button_photo = ImageTk.PhotoImage(button_image)

    # Create the button with the image
    image_button = tk.Button(home_frame, image=button_photo, command=open_change_password_dialog, bg="#333333", bd=0)
    
    # Position the button below the title label
    title_label.update_idletasks()  # Ensure the title label has been drawn and has a size
    title_label_height = title_label.winfo_height()  # Get the height of the title label
    button_y_position = title_label.winfo_y() + title_label_height + 10  # Add some padding below the title

    # Position the button using place
    image_button.place(relx=0.5, rely=button_y_position / home_frame.winfo_height(), anchor='center')  # Center horizontally and position below the title

    # Adjust the button's position to shift it to the southeast
    image_button.place(x=image_button.winfo_x() + 500, y=image_button.winfo_y() + 40)  # Move southeast by 20 pixels

    # Keep a reference to avoid garbage collection
    image_button.image = button_photo

def fetch_report_data(engine):
    query = "SELECT crop, soiltype, description, irrig, season, steps FROM report"
    report_df = pd.read_sql_query(query, engine)
    return report_df

def delete_crop(crop_name):
    conn = connect_to_db()
    try:
        with conn.connect() as connection:
            delete_query = text("DELETE FROM report WHERE crop = :crop_name")
            connection.execute(delete_query, {'crop_name': crop_name})
            connection.commit()  # Commit the transaction
            messagebox.showinfo("Success", f"Crop '{crop_name}' has been deleted.")
    except Exception as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

def report_page():
    clear_frame()  # Clear the current frame
    report_frame = tk.Frame(main_frame, bg="#333333")
    report_frame.pack(fill=tk.BOTH, expand=True)

    # Create a frame for the header (to hold the title and reload button)
    header_frame = tk.Frame(report_frame, bg="#333333")
    header_frame.pack(fill=tk.X)  # Fill the width of the report frame

    # Add the title label to the header frame
    title_label = tk.Label(header_frame, text="Report", font=tkFont.Font(family="Georgia", size=50, weight="bold", underline=True), bg="#333333", fg="#00FF00")
    title_label.pack(side=tk.TOP, padx=10, pady=10)  # Place on the top with padding

    # Add a reload button to the header frame
    reload_button = tk.Button(header_frame, text="Reload", command=lambda: report_page(), bg="#4CAF50", fg="#ffffff")
    reload_button.pack(side=tk.RIGHT, padx=10, pady=10)  # Place on the right side with padding

    # Create a canvas for scrolling
    canvas = tk.Canvas(report_frame, bg="#333333")
    scrollable_frame = tk.Frame(canvas, bg="#333333")

    # Create a vertical scrollbar
    scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a window in the canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="n")  # Anchor to the north

    # Update the scroll region of the canvas
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_configure)

    # Connect to the database and fetch report data
    conn = connect_to_db()
    report_df = fetch_report_data(conn)

    # Create tiles for each record in the report
    for index, row in report_df.iterrows():
        crop_name = row['crop']
        soil_type = row['soiltype']
        irrigation_type = row['irrig']
        season = row['season']
        steps = row['steps']

        # Create a frame for the tile to hold the label and button
        tile_frame = tk.Frame(scrollable_frame, bg="#444444", relief=tk.RAISED, bd=2, width=600)  # Darker background for tile
        tile_frame.pack(padx=10, pady=10, anchor='center')  # Center the tile frame

        # Create the tile label with the crop name as the heading
        heading_label = tk.Label(tile_frame, text=crop_name, font=("Arial", 16, "bold"), bg="#444444", fg="#ffffff")
        heading_label.pack(pady=(10, 5))  # Add some padding at the top

        # Create additional information labels
        info_label = tk.Label(tile_frame, text=f"Soil Type: {soil_type}\n"
                                                f"Irrigation Requirements: {irrigation_type}\n"
                                                f"Season: {season}\n"
                                                f"Steps: {steps}",
                              bg="#444444", fg="#ffffff", wraplength=580)  # Match label background with tile
        info_label.pack(padx=10, pady=(0, 10))  # Add padding around the info label

        # Create the delete button
        delete_button = tk.Button(tile_frame, text="Delete", bg="#ff4d4d", fg="#ffffff",
                                   command=lambda name=crop_name: delete_crop(name))
        delete_button.pack(side=tk.BOTTOM, padx=10, pady=5)

    # Center the scrollable frame in the canvas
    scrollable_frame.update_idletasks()  # Update the frame to get its width
    canvas_width = canvas.winfo_width()
    frame_width = scrollable_frame.winfo_width()
    x = (canvas_width - frame_width) // 2  # Calculate x position to center
    canvas.create_window((x, 0), window=scrollable_frame, anchor="n")  # Recreate the window with new x position

    # Center the content in the scrollable frame
    for widget in scrollable_frame.winfo_children():
        widget.pack(side=tk.TOP, anchor='center')  # Center-align each widget

    # Update the scroll region of the canvas
    report_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

def create_tile(parent, title, content):
    tile_frame = tk.Frame(parent, bg="#444444", bd=2, relief=tk.RAISED, width=600)
    tile_frame.pack(pady=10, padx=10, fill=tk.X)

    title_label = tk.Label(tile_frame, text=title, font=("Arial", 16, "bold"), bg="#444444", fg="#ffffff")
    title_label.pack(pady=5)

    content_label = tk.Label(tile_frame, text=content, bg="#444444", fg="#ffffff", wraplength=580)
    content_label.pack(pady=5)

    return tile_frame

def about_page():
    clear_frame()
    
    # Create a main frame for the about page
    about_frame = tk.Frame(main_frame, bg="#333333")
    about_frame.pack(fill=tk.BOTH, expand=True)

    # Create a canvas for scrolling
    canvas = tk.Canvas(about_frame, bg="#333333")
    scrollable_frame = tk.Frame(canvas, bg="#333333")

    # Create a vertical scrollbar
    scrollbar = ttk.Scrollbar(about_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a window in the canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="n")  # Anchor to the north

    # Update the scroll region of the canvas
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_configure)

    # Add the title label
    label = tk.Label(scrollable_frame, text="About", font=tkFont.Font(family="Georgia", size=50, weight="bold", underline=True), bg="#333333", fg="#00FF00")
    label.pack(pady=20)

    conn = connect_to_db()
    
    # Fetch details for the first tile
    about_df = fetch_details(conn)  # Use the updated function

    for index, row in about_df.iterrows():
        detail_text = row['details']
        create_tile(scrollable_frame, f"About", detail_text) 

    # Fetch writeup from credits table
    credits_df = fetch_credits(conn)  # Fetch the writeup from credits table
    if not credits_df.empty:
        writeup_text = credits_df.iloc[0]['writeup']  # Get the first writeup
        create_tile(scrollable_frame, "Credits", writeup_text)  # Create a new tile for the writeup


    # Center the scrollable frame in the canvas
    scrollable_frame.update_idletasks()  # Update the frame to get its width
    canvas_width = canvas.winfo_width()
    frame_width = scrollable_frame.winfo_width()
    x = (canvas_width - frame_width) // 2  # Calculate x position to center
    canvas.create_window((x, 0), window=scrollable_frame, anchor="n")  # Recreate the window with new x position

    # Center the content in the scrollable frame
    for widget in scrollable_frame.winfo_children():
        widget.pack(side=tk.TOP, anchor='center')  # Center-align each widget

def clear_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()

# Initialize main application
root = tk.Tk()
root.geometry("1350x750")
root.title("Harvest Hub")

main_frame = tk.Frame(root, bg="#333333")
options_frame = tk.Frame(root, bg ="#222222")

# Setup main frame
main_frame.place(x=250, y=0, width=1100, height=750)
options_frame.place(x=0, y=0, width=250, height=750)

# Navigation buttons
home_button = tk.Button(options_frame, width=20, text="Home", font=("bold", 15), fg="#1DB954", bg="#333333",
                        command=home_page)
home_button.place(x=10, y=100)

cropfilter_button = tk.Button(options_frame, width=20, text="Crop Filter", font=("bold", 15), fg="#1DB954",
                              bg="#333333", command=cropfilter_page)
cropfilter_button.place(x=10, y=175)

report_button = tk.Button(options_frame, width=20, text="Report", font=("bold", 15), fg="#1DB954", bg="#333333",
                          command=report_page)
report_button.place(x=10, y=250)

about_button = tk.Button(options_frame, width=20, text="About", font=("bold", 15), fg="#1DB954", bg="#333333",
                      command=about_page)
about_button.place(x=10, y=325)

# Start with the home page
home_page()

root.mainloop()
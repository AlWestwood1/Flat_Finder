from bs4 import BeautifulSoup
import requests
import re
import os.path
from discord import SyncWebhook
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
import webbrowser


webhook = SyncWebhook.from_url("https://discord.com/api/webhooks/995441714842063000/eR67iNsRAeDgF468Z2P5bdCcQpcGS2oSsG4TrD656RjPv0RaJApaWWgL6pqQrtJozH3w")

base_dir = os.path.dirname(__file__)
lists_dir = os.path.join(base_dir, "property_lists")

#Converts list to txt
def list_to_txt(list_in, filename):
    path = os.path.join(lists_dir, filename)
    file = open(path, "w")

    for i in list_in:
        file.write("%s\n" % i)
    print("Writing to file complete\n\n")


#Converts txt to list
def txt_to_list(filename):
    root = "/Users/alistairwestwood/Documents/VS Code/"
    path = os.path.join(lists_dir, filename)
    file = open(path, "r")
    file_list = []

    for line in file:
        l = line[:-1]
        file_list.append(l)

    return file_list


#Finds properties with desired specs
def rm_get_properties (LocationID, min_price, max_price, radius, isFurnished, min_room, max_room):

    #If furnished only was selected, add parameter to url
    if isFurnished == True:
        rm_url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%{LocationID}&maxBedrooms={max_room}&minBedrooms={min_room}&maxPrice={max_price}&minPrice={min_price}&radius={radius}&propertyTypes=&mustHave=&dontShow=&furnishTypes=furnished%2CpartFurnished&keywords='
    else:
        rm_url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%{LocationID}&maxBedrooms={max_room}&minBedrooms={min_room}&maxPrice={max_price}&minPrice={min_price}&radius={radius}&propertyTypes=&mustHave=&dontShow=&furnishTypes=&keywords='
    
    rm = requests.get(rm_url)
    rm_doc = BeautifulSoup(rm.text, "html.parser")


    #Find all properties on first page
    tiles = rm_doc.find_all(["div"], id=re.compile("property-"))

    id_list = []

    #Extract property ids
    for i in range (1, len(tiles)):
        id = tiles[i]['id'].removeprefix("property-")
        if id != '0':
            id_list.append(id)

    return id_list

#Compare the old list with the new
def rm_compare(new_list):
    old_list = txt_to_list("rm_old.txt")
    new_flats = list(set(new_list).difference(old_list))

    #Save the new list as the old list name to complete the cycle
    list_to_txt(new_list, "rm_old.txt")
    
    return new_flats

#Find the URL of the new properties
def rm_find_URL(list):
    url_list = []
    for i in range (0,len(list)-1):
        id = list[i]
        url_list.append(f"https://www.rightmove.co.uk/properties/{id}#/?channel=RES_LET")
    
    return url_list

#Post all new properties to discord
def discord_post(url_list):
    for url in url_list:
        webhook.send("A new flat has been found!\n\n"+ url + "\n")
        print("Posted to discord\n")



def main():
    rm_list = rm_get_properties(LocationID, min_price, max_price, radius, isFurnished, min_room, max_room)
    #print(rm_list, "\n\n")
    print(len(rm_list), "results found\n")


    rm_new_flats = rm_compare(rm_list)
    if len(rm_new_flats) > 0:
        rm_url_list = rm_find_URL(rm_new_flats)
        discord_post(rm_url_list)

    window.after(int(refresh_rate)*60000, main)
    
#Holborn = 5E87513
#Bloomsbury = 5E87494



def submit_form():

    global LocationID
    global min_price
    global max_price
    global radius
    global min_room
    global max_room
    global isFurnished
    global refresh_rate

    # Get the values from the input
    LocationID = LocID_entry.get().upper()
    min_price = min_price_entry.get()
    max_price = max_price_entry.get()
    radius = radius_variable.get()
    min_room = min_room_variable.get()
    max_room = max_room_variable.get()
    isFurnished = furnished_var.get()
    refresh_rate = refresh_entry.get()

    ### ERROR HANDLING ###

    #Initialise string for error message
    errors = ""

    #Check http status code is correct
    url = f"https://www.rightmove.co.uk/property-to-rent/find.html?searchType=RENT&locationIdentifier=REGION%{LocationID}&insId=1&radius=0.0&minPrice=&maxPrice=&minBedrooms=&maxBedrooms=&displayPropertyType=&maxDaysSinceAdded=&sortByPriceDescending=&_includeLetAgreed=on&primaryDisplayPropertyType=&secondaryDisplayPropertyType=&oldDisplayPropertyType=&oldPrimaryDisplayPropertyType=&letType=&letFurnishType=&houseFlatShare="
    r = requests.head(url)
    print(r.status_code)

    if r.status_code == 400:
        errors = errors + "Invalid location ID\n"

    #Check min price is valid
    if not min_price.isdigit():
        errors = errors + "Invalid minimum price\n"

    #Check max price is valid
    if not max_price.isdigit():
        errors = errors + "Invalid maximum price\n"

    #Check refresh rate is valid
    if not refresh_rate.isdigit():
        errors = errors + "Invalid refresh rate\n"

    #Check if any errors exist, if so print error message
    if errors != "":
        error_msg = "The following inputs are invalid:\n" + errors
        messagebox.showinfo("Error", error_msg)
    
    #If no errors exist show page 2
    else:
        ### PAGE 2 CONTENTS ###
        params = Label(page2, text=f"  Location: {LocationID}\n  Minimum Price: £{min_price}\n  Maximum Price: £{max_price}\n  Radius: {radius} miles\n  Minimum Bedrooms: {min_room}\n  Maximum Bedrooms: {max_room}\n  Only searching for furnished properties: {isFurnished}", anchor="e", justify=LEFT)
        params.grid(row=1, column=0, rowspan=1)

        page2.tkraise()
        window.after(int(refresh_rate)*60000, main)
        




# Create the main window
window = Tk()
window.title("FlatFinder")

page1 = Frame(window)
page2 = Frame(window)

page1.grid(row=0, column=0, sticky="nsew")
page2.grid(row=0, column=0, sticky="nsew")
page1.lift()

for i in range(3):
    page1.columnconfigure(i, weight=1, minsize=200)
    page1.rowconfigure(i, weight=1, minsize=35)

for i in range(3):
    page2.columnconfigure(i, weight=1, minsize=200)
    page2.rowconfigure(i, weight=1, minsize=35)

# PAGE 1 LABELS
LocID_label = Label(page1, text="Location ID:")
LocID_label.grid(row=0, column=0)
min_price_label = Label(page1, text="Minimum Price:")
min_price_label.grid(row=1, column=0)
max_price_label = Label(page1, text="Maximum Price:")
max_price_label.grid(row=2, column=0)
radius_label = Label(page1, text="Radius:")
radius_label.grid(row=3, column=0)
min_room_label = Label(page1, text="Minimum beds (0 for studio):")
min_room_label.grid(row=4, column=0)
max_room_label = Label(page1, text="Maximum beds (0 for studio):")
max_room_label.grid(row=5, column=0)
furnished_label = Label(page1, text="Only view furnished properties?")
furnished_label.grid(row=6, column=0)

#PAGE 1 INPUTS
LocID_entry = Entry(page1)
LocID_entry.grid(row=0, column=1)
min_price_entry = Entry(page1)
min_price_entry.grid(row=1, column=1)
max_price_entry = Entry(page1)
max_price_entry.grid(row=2, column=1)
radius_options = [0, 0.25, 0.5, 1, 3, 5, 10, 15, 20, 30, 40,]
radius_variable = DoubleVar()
radius_variable.set(radius_options[0])
radius_chosen = OptionMenu(page1, radius_variable, *radius_options)
radius_chosen.grid(row=3, column=1)
room_options = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
min_room_variable = IntVar()
min_room_variable.set(room_options[0])
min_room_chosen = OptionMenu(page1, min_room_variable, *room_options)
min_room_chosen.grid(row=4, column=1)
max_room_variable = IntVar()
max_room_variable.set(room_options[0])
max_room_chosen = OptionMenu(page1, max_room_variable, *room_options)
max_room_chosen.grid(row=5, column=1)
furnished_var = BooleanVar()
furnished_entry = Checkbutton(page1, variable=furnished_var)
furnished_entry.grid(row=6, column=1)

#Refresh rate labels/input
refresh_label = Label(page1, text="Refresh frequency (in mins):")
refresh_label.grid(row=6, column=2)
refresh_entry = Entry(page1)
refresh_entry.grid(row=6, column=3)


#Title and info text
title = Label(page1, text="Welcome to FlatFinder!", font=('Helvetica', 18, 'bold'))
title.grid(row=0, column=2, columnspan=3)
ID_desc = Label(page1, text="To find the location ID, follow these steps:\n1. On Rightmove, search for properties in the desired location.\n2. Look for the values after REGION% (shown below).\n3. Copy these values into the Location ID box in FlatFinder.", anchor="e", justify=LEFT)
ID_desc.grid(row=1, column=2, columnspan=3, rowspan=3)

#Image of location ID
img_frame = Frame(page1)
img_frame.grid(row=4, column=2, columnspan=2, rowspan=1)
img = ImageTk.PhotoImage(Image.open("location_id_img.jpg"))
img_label = Label(img_frame, image = img)
img_label.pack(padx=(15, 15))

# Search button
submit_button = Button(page1, text="Search", command=submit_form)
submit_button.grid(row=7, column=0, columnspan=5)


### PAGE 2 INDEPENDENT CONTENTS ###
pg2_subtitle = Label(page2, text="Your chosen parameters:", font=('Helvetica', 14, 'bold'))
pg2_subtitle.grid(row=0, column=0)

pg2_title = Label(page2, text="Flatfinder is Running", font=('Helvetica', 18, 'bold'))
pg2_title.grid(row=0, column=1)

pg2_desc = Label(page2, text="Add this discord bot to your server to be notified when FlatFinder\nfinds new properties!")
pg2_desc.grid(row=1, column=1)
bot_link = Label(page2, text="Discord bot", font=('Helvetica', 14, 'bold'),  fg="blue")
bot_link.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://discord.com/api/oauth2/authorize?client_id=995437148025126962&permissions=274878089216&scope=bot"))
bot_link.grid(row=2, column=1)

# Start the main loop
window.mainloop()
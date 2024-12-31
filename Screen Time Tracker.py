import psutil
import win32gui
import tkinter as tk
from tkinter import ttk
from datetime import datetime,timedelta,date
import sqlite3
import random
import threading
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageDraw
from pystray import Icon, MenuItem, Menu
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import time
import os
import platform
from tkinter import scrolledtext


conn = sqlite3.connect('app_usage.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY,
                    app_name TEXT,
                    usage_date DATE,
                    usage_count INTEGER
                )''')
cursor.execute("INSERT INTO app_usage (app_name, usage_date, usage_count) VALUES ('{}', '{}', {})".format(str(date.today),"31-12-2024",8))
conn.commit()
conn.close()

def display_info_in_scrolled_text(frame, info):
    # Create a scrolled text widget inside the given frame
    
    # Function to update text in the scrolled text box
    def update_text(): # Clear any existing text
        text_box.insert(tk.END, info+"\n")  # Insert the new info

    # Create a thread to update the text
    thread = threading.Thread(target=update_text)
    thread.start()


file=open("logs.txt","a")
#gets the currently viewed window
def get_active_window_title():
    active_window = win32gui.GetForegroundWindow()
    window_title = win32gui.GetWindowText(active_window)
    return window_title

#logs the data of duration of usage of the window
def log_usage(interval, duration):
    
    global fd,file
    try:
        del fd['Please Start Logging']
    except:pass

    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        active_window_title = get_active_window_title()
        if active_window_title:
            x=active_window_title
            display_info_in_scrolled_text(logframe,x)
            file.write(active_window_title+"\n")
            if  x in fd:
                fd[x] += interval
            else:
                fd[x] = interval
        time.sleep(interval)
        file.flush()

#To pick just the app name from the active_window_title
def correctapp(a):
    return a.split('- ')[-1]

#calculates most used app for showing it in the home_screen
def mostusedapp():
    global fd
    str1=""
    try:
        maxi=max(fd.values())
        for i in fd:
            if fd[i]==maxi:
                str1=i
                break
        return str1
    except:
        return "Please start Logging"

#Calculates total screen time
def totaltime():
    global fd
    s=sum(fd.values())
    return timeformat(s)

#Converts seconds into required time format
def timeformat(s):
    h=""
    m=""
    if s>=60:
        m=s//60
        s=s%60
    if type(m)==int and m>=60:
        h=str(m//60)+"h "
        m=str(m%60)+"m "
    if type(m)==int and m!=0:
        m=str(m)+"m "
    return h+m+str(s)+'s'

#saves today's data once close button is pressed
def savedb():
    global fd,file
    conn = sqlite3.connect('app_usage.db')
    cursor = conn.cursor()
    today = date.today()            
    cursor.execute("DELETE FROM app_usage WHERE usage_date='"+str(today)+"'")
    def log_app_usage(app_name, usage_count):
        today = date.today()
        cursor.execute("INSERT INTO app_usage (app_name, usage_date, usage_count) VALUES ('{}', '{}', {})".format(app_name,str(today),usage_count))
    for i in fd:
        log_app_usage(i,fd[i])
    conn.commit()
    file.close()

#retrieves today's data alone initially when the app first starts
def retrieve_todays_data():
    global fd
    try:
        conn = sqlite3.connect('app_usage.db')
        cursor = conn.cursor()
        cursor.execute("SELECT app_name,usage_count FROM 'app_usage' WHERE usage_date=Date('now')")
        rows = cursor.fetchall()
        # Storing key-value pairs in a dictionary
        data_dict = {}
        for row in rows:
            key, value = row
            data_dict[key] = value

        # Close the connection
        conn.close()
        del fd["Please Start Logging"]
        fd.update(data_dict)
    except:pass

#function to create the list of past 10 days
past_dates_list=[]
def past_dates():
    global past_dates_list
    # Get the current date
    current_date = datetime.now().date()

    # Loop through the past 10 days
    for i in range(10, 0, -1):
        past_date = current_date - timedelta(days=i)
        past_dates_list.append(past_date)
    past_dates_list.append(current_date)
    return past_dates_list[::-1][2:]

#function to convert date list into alpha  numberic date list
a=[]
def alpha_past_dates():
    global a
    a=past_dates()
    d1={'01':"January",'02':'February','03':'March','04':'April','05':'May','06':'June','07':'July','08':'August','09':'September','10':'October','11':'November','12':'December'}
    for i in range(len(a)):
        x=str(a[i]).split('-')
        a[i]=x[-1]+" "+d1[x[1]]+" "+x[0]
    else:
        a=['Today',"Yesterday"]+a
    return a


#Starting and stopping data storage
stop_thread = threading.Event()
thread=None
def update_label():
    while not stop_thread.is_set():
        log_usage(1,1)
        time.sleep(0.025) 

def toggle_update_thread():
    global thread
    if not thread or not thread.is_alive():
        # Start the thread
        stop_thread.clear()
        thread = threading.Thread(target=update_label)
        thread.daemon = True  # Daemonize thread to close it with the main program
        thread.start()
        start_button.configure(text="Stop",fg_color="#d1567d", hover_color="#8c3a54")
    else:
        # Stop the thread
        stop_thread.set()
        start_button.configure(text="Start",fg_color="#5b638f",hover_color="#4c5375")

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        print("Window closed.")
        # Call your function here
        savedb()
        window.destroy()
        

#Combobox handling
other_date_selected=False
def convert_date_back(x):
    global other_date_selected
    if x=="Today":other_date_selected=False
    else:other_date_selected=True
    otherdaydata(past_dates_list[a[::-1].index(x)])

def page2_controls_mostapp():
    global other_date_selected
    if other_date_selected==True:
        return mostused_app_other()
    else:
        return mostusedapp()

def page2_controls_tt():
    global other_date_selected
    if other_date_selected==True:
        return totaltime_other()
    else:
        return totaltime()


def mostused_app_other():
    global other_day_data
    str1=""
    try:
        maxi=max(other_day_data.values())
        for i in other_day_data:
            if other_day_data[i]==maxi:
                str1=i
                break
        return str1
    except:
        return "No Data Found"


#Calculates total screen time
def totaltime_other():
    global other_day_data
    s=sum(other_day_data.values())
    return timeformat(s)


#retreiving data of other days
other_day_data={}
def otherdaydata(otherdate):
    global other_day_data
    try:
        conn = sqlite3.connect('app_usage.db')
        cursor = conn.cursor()
        cursor.execute("SELECT app_name,usage_count FROM app_usage WHERE usage_date='{}'".format(str(otherdate)))
        rows = cursor.fetchall()
        # Storing key-value pairs in a dictionary
        data_dict = {}
        for row in rows:
            key, value = row
            data_dict[key] = value

        # Close the connection
        conn.close()
        other_day_data=data_dict
    except:pass

# Function to create an icon for the system tray
def create_image():
    # Create a simple black square as the tray icon
    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)
    image = Image.open(relative_to_assets("tbar logo.png"))
    draw = ImageDraw.Draw(image)
    return image

# Function to show the window from the tray
def show_window(icon, item):
    icon.stop()
    window.after(0, restore_window)

# Function to restore the window geometry
def restore_window():
    window.geometry(window.geometry_saved)
    window.deiconify()

# Function to hide the window to the system tray
def hide_window():
    window.geometry_saved = window.geometry()  # Save the current window geometry
    window.withdraw()
    menu = Menu(
        MenuItem('Show', show_window)
    )
    icon = Icon("Screen Time Tracker", create_image(), "Screen Time Tracker", menu)
    threading.Thread(target=icon.run).start()

if __name__ == "__main__":
    def show_loading_screen():
        from tkinter import PhotoImage,Canvas,Tk,Label
        from pathlib import Path
        from PIL import Image, ImageTk
        splash_root = tk.Tk()
        window_width = 500
        window_height = 425
        loading=Canvas(splash_root)


        screen_width = splash_root.winfo_screenwidth()
        screen_height = splash_root.winfo_screenheight()

        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)

        splash_root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")


        OUTPUT_PATH = Path(__file__).parent
        ASSETS_PATH = OUTPUT_PATH / Path(r"build\assets\frame0")
        def relative_to_assets(path: str) -> Path:
            return ASSETS_PATH / Path(path)
         # Replace with your image file path

    # Add the image to a Label widget
        img1=Image.open(relative_to_assets("logo.png"))
        img2= img1.resize((350, 240)) 
        img = ImageTk.PhotoImage(img2) 
        label = tk.Label(splash_root, image=img)
        label.pack(pady=20)


        quotes = [
            "To infinity and beyond!",
            "The sky is not the limit.",
            "One small step for man, one giant leap for mankind.",
            "To be or not be, that is the question",
            "Success is when your signature changes into an autograph."
        ]

        # Loading text label
        splash_label = tk.Label(splash_root, text=random.choice(quotes), font=("Helvetica", 12))
        splash_label.pack(pady=20)

        # Progress bar
        progress = ttk.Progressbar(splash_root, orient="horizontal", length=300, mode="determinate")
        progress.pack(pady=20)

        # Update the progress bar gradually
        splash_root.update_idletasks()  # Ensure screen elements are drawn
        for i in range(100):
            progress['value'] = i + 1   # Update the progress bar value
            splash_root.update()        # Refresh the window to show progress
            time.sleep(0.03)            # Adjust the delay for speed of loading

        splash_root.destroy()  # Close splash screen after loading completes

    show_loading_screen()
    fd={"Please Start Logging":0}
    retrieve_todays_data()

    from pathlib import Path

    # from tkinter import *
    # Explicit imports to satisfy Flake8
    from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage,ttk

    OUTPUT_PATH = Path(__file__).parent
    ASSETS_PATH = OUTPUT_PATH / Path(r"build\assets\frame0")

    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    window = Tk()
    window.title("Screen Time Tracker")

    window.geometry("1000x580")
    window.configure(bg = "#1E1E1E")

    photo = PhotoImage(file = relative_to_assets("tbar logo.png"))
    window.iconphoto(False, photo)

    home=ttk.Notebook(window)#tab1
    treeframe=Canvas(
        window,
        bg = "#1E1E1E",
        height = 550,
        width = 1000,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    logframe=Canvas(
        window,
        bg = "#1E1E1E",
        height = 550,
        width = 1000,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    canvas = Canvas(
        window,
        bg = "#1E1E1E",
        height = 550,
        width = 1000,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    canvas.place(x = 0, y = 0)
    image_image_1 = PhotoImage(
        file=relative_to_assets("image_1.png"))
    image_1 = canvas.create_image(
        500.0,
        40.0,
        image=image_image_1
    )
    

    image_image_2 = PhotoImage(
        file=relative_to_assets("tbar logo.png"))
    image_2 = canvas.create_image(
        275.0,
        40.0,
        image=image_image_2
    )


    image_image_4 = PhotoImage(
        file=relative_to_assets("image_4.png"))
    image_4 = canvas.create_image(
        497.0,
        381.0,
        image=image_image_4
    )

    canvas.create_text(
        70.0,
        3.0,
        anchor="nw",
        text="Screen Time \nTracker",
        fill="#FFFFFF",
        font=("Inter Bold", 30 * -1)
    )

    image_image_5 = PhotoImage(
        file=relative_to_assets("image_5.png"))
    image_5 = canvas.create_image(
        276.0,
        147.0,
        image=image_image_5
    )

    canvas.create_text(
        110.0,
        114.0,
        anchor="nw",
        text="Total Time used today:  ",
        fill="#FFFFFF",
        font=("Inter Bold", 24 * -1)
    )

    image_image_6 = PhotoImage(
        file=relative_to_assets("image_6.png"))
    image_6 = canvas.create_image(
        411.0,
        149.0,
        image=image_image_6
    )

    tt=canvas.create_text(
        113.0,
        152.0,
        anchor="nw",
        text=totaltime(),
        fill="#FFFFFF",
        font=("Inter Bold", 24 * -1)
    )

    image_image_7 = PhotoImage(
        file=relative_to_assets("image_7.png"))
    image_7 = canvas.create_image(
        711.0,
        147.0,
        image=image_image_7
    )

    canvas.create_text(
        560.0,
        111.0,
        anchor="nw",
        text="Most Used App: ",
        fill="#000000",
        font=("Inter Bold", 24 * -1)
    )

    image_image_8 = PhotoImage(
        file=relative_to_assets("image_8.png"))
    image_8 = canvas.create_image(
        834.0,
        147.0,
        image=image_image_8
    )

    mostapp=canvas.create_text(
        557.0,
        150.0,
        anchor="nw",
        text=mostusedapp(),
        fill="#000000",
        font=("Inter Bold", 24 * -1)
    )
    #Treeframe canvas ui starts here
    most_used_app_bg2 = treeframe.create_image(
        720.0,
        345.0,
        image=image_image_7
    )
    treeframe.create_text(
        575.0,
        310.0,
        anchor="nw",
        text="Most Used App: ",
        fill="#000000",
        font=("Inter Bold", 24 * -1)
    )    
    mostapp_2=treeframe.create_text(
        575.0,
        350.0,
        anchor="nw",
        text=page2_controls_mostapp(),
        fill="#000000",
        font=("Inter Bold", 24 * -1)
    )    

    mostapp2=treeframe.create_image(
        850.0,
        352,
        image=image_image_8
    )
 #tt
    image_5_2 = treeframe.create_image(
        280.0,
        352.0,
        image=image_image_5
    )   


    treeframe.create_text(
        130,
        310,
        anchor="nw",
        text="Total Time Used: ",
        fill="#FFFFFF",
        font=("Inter Bold", 24 * -1)
    )


    tt_2 = treeframe.create_image(
        425,
        352,
        image=image_image_6
    )

    tt_3 = treeframe.create_text(
        130,
        350,
        anchor="nw",
        text=page2_controls_tt(),
        fill="#FFFFFF",
        font=("Inter Bold", 24 * -1)
    )




    #UPDATING UI ELEMENTS
    st=False
    def updatetime():
        if st==True:
            canvas.itemconfig(tt,text=totaltime())
            canvas.after(40,updatetime)

            
    def updateapp():
        global c
        canvas.itemconfig(mostapp,text=mostusedapp())
        canvas.after(1000,updateapp)
        tree.after(100,treev)
        treeframe.itemconfig(tt_3,text=page2_controls_tt())
        treeframe.itemconfig(mostapp_2,text=page2_controls_mostapp()) 
        
    def start():
        global st
        st=True
        updatetime()


    def stop():
        global st
        st=False
        updatetime()
    

    

   #Start and Stop
    start_button = ctk.CTkButton(
        canvas, 
        text="Start", 
        command=lambda:[start(),toggle_update_thread()],
        text_color="white",
        fg_color="#5b638f", 
        hover_color="#4c5375",
        corner_radius=10,
        height=35,
        width=93
    )
    start_button.place(x=550,y=10)
    

    #Treeview Table
    tree = ttk.Treeview(treeframe, columns=('Usage'))
    tree.heading('#0', text='App Name')
    tree.heading("#1",text="Usage")
    tree.column('#0', width=5, anchor='w',minwidth=1)
    tree.column("#1",width=10,anchor="center",minwidth=20)

    #graph
    class GraphUpdater:
        def __init__(self, canvas, title="Pie Chart", width=400, height=300, x=0, y=0, chart_bg_color="white"):
            global fd
            # Initialize instance variables
            self.canvas = canvas
            self.title = title
            self.width = width
            self.height = height
            self.x = x
            self.y = y
            self.chart_bg_color = chart_bg_color
            self.running = False  # Thread control flag
            
            # Sample initial data for the pie chart
            self.data =data= sorted(list(fd.values()),reverse=True)[0:5]
            labels=[]
            for j in data:
                for i in fd:
                    if fd[i]==j and i not in labels:
                        labels.append(i)
            self.labels = labels
            self.colors = ["#d9d9d9", "#87CEEB", "#98FB98", "#FFD700", "#FF6347"]

            # Embed the initial pie chart
            self.embed_pie_chart()
            
        def embed_pie_chart(self):
            # Clear previous figure if any
            if hasattr(self, 'figure_canvas'):
                self.figure_canvas.get_tk_widget().destroy()

            # Create a new matplotlib figure
            self.fig = Figure(figsize=(self.width / 100, self.height / 100), dpi=100, facecolor=self.chart_bg_color)
            self.ax = self.fig.add_subplot(111, facecolor=self.chart_bg_color)
            
            # Create a pie chart
            self.pie=self.ax.pie(
                self.data, 
                labels=self.labels, 
                colors=self.colors, 
                autopct='%1.1f%%',
                startangle=140,
                pctdistance=0.85,
                labeldistance=1.1
            )
            self.ax.set_title(self.title)

            # Embed the matplotlib figure in the tkinter canvas
            self.figure_canvas = FigureCanvasTkAgg(self.fig, master=self.canvas)
            self.figure_canvas.draw()
            widget = self.figure_canvas.get_tk_widget()
            widget.place(x=self.x, y=self.y, width=self.width, height=self.height)

        def update_data(self):
            # Function to update data continuously in a thread
            while self.running:
                # Example: Update data values (you can replace this with actual data fetching)
                self.data=data=sorted(list(fd.values()),reverse=True)[0:5]
                labels=[]
                for j in data:
                    for i in fd:
                        if fd[i]==j and i not in labels:
                            labels.append(i)
                
                self.labels=sorted(labels)[0:5]
                # Clear the existing chart but retain the axis and figure
                self.ax.clear()
                self.ax.set_facecolor(self.chart_bg_color)
                
                # Redraw the pie chart with updated data
                self.pie = self.ax.pie(
                    self.data, 
                    labels=self.labels, 
                    colors=self.colors, 
                    autopct='%1.1f%%',
                    startangle=140,
                    pctdistance=0.85,
                    labeldistance=1.1
                )
                self.ax.set_title(self.title)
                
                # Update the canvas without flickering
                self.figure_canvas.draw_idle()
                
                # Sleep for the specified update interval
                time.sleep(0.1)

        def start_updating(self):
            # Start the update thread
            self.running = True
            self.update_thread = Thread(target=self.update_data)
            self.update_thread.daemon = True  # Daemonize thread to end it with main program
            self.update_thread.start()

        def stop_updating(self):
            # Stop the update thread
            self.running = False
            self.update_thread.join()
    graph_updater = GraphUpdater(canvas, title="Your Usage:", width=700, height=312, x=150, y=220, chart_bg_color="#e1e395")
    graph_updater.start_updating()

    def treev():
        tree.delete(*tree.get_children())

        style = ttk.Style()
    
    # Configure the Treeview Heading style
        style.configure("Treeview.Heading", 
                        font=("Helvetica", 10 ),
                        background="white",
                        foreground="black")
        if other_date_selected==False:
            x=fd
        else:
            x=other_day_data
        try:
            for i in x:
                if fd[i]>7:
                    tree.insert("", "end",text=i, values=(timeformat(x[i]),))
        except:pass
        
        tree.tag_configure('oddrow', background='#525454',foreground="white")
        tree.tag_configure('evenrow', background='#181818', foreground='white')

        # Apply the tags to the rows
        for i, item in enumerate(tree.get_children()):
            if i % 2 == 0:
                tree.item(item, tags=('evenrow',))
            else:
                tree.item(item, tags=('oddrow',))

    
    #date selector
    def combobox(value):
        convert_date_back(f"{value}")
    date_select=ctk.CTkComboBox(treeframe,values=alpha_past_dates(),fg_color="black",border_color="#ba950f",
    dropdown_fg_color="#005ba1",dropdown_hover_color="#ba950f",corner_radius=5,command=combobox)
    date_select.pack(pady=10)

    tree.place(x=200,y=200)
    tree.pack(expand=False, fill='both',padx=100,pady=20)
    
    hide_button=ctk.CTkButton(canvas,
    text="Hide To Tray",command=hide_window,
    text_color="white",
    fg_color="#32bf8e", 
    hover_color="#377861",
    corner_radius=10,
    height=35,
    width=100
    )
    hide_button.place(x=680,y=10)

    def create_pie_chart_window(title="Your Usage"):
        global other_day_data
        data=sorted(list(other_day_data.values()),reverse=True)[0:5]
        labels=[]
        for j in data:
            for i in other_day_data:
                if other_day_data[i]==j and i not in labels:
                    labels.append(i)
        colors = ["#d9d9d9", "#87CEEB", "#98FB98", "#FFD700", "#FF6347"]
        # Create a new Tkinter window for the pie chart
        chart_window = tk.Toplevel()
        chart_window.title(title)
        chart_window.geometry("600x400")
        
        # Create a matplotlib figure and axis
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Plot the pie chart on the axis
        ax.pie(
            data,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',  # Display percentages
            startangle=140,     # Rotate the start angle for better layout
            pctdistance=0.85,   # Adjust percentage text distance
            labeldistance=1.1   # Adjust label text distance
        )
        ax.set_title(title)
        
        # Embed the matplotlib figure into the Tkinter window
        chart_canvas = FigureCanvasTkAgg(fig, master=chart_window)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    

        
    home.add(canvas,text="Home")
    home.add(treeframe,text="Advanced")
    home.add(logframe,text="Log")
    home.pack()



    def graph_button_handling():
        global other_date_selected
        if other_date_selected==True:
            create_pie_chart_window()
        else:
            home.select(home.index(canvas))

    graph_button = ctk.CTkButton(
        treeframe, 
        text="View in Pie Chart", 
        command=lambda:graph_button_handling(),
        text_color="black",
        fg_color="#ffd700", 
        hover_color="#4c5375",
        corner_radius=10,
        height=50,
        width=250
    )


    def open_text_file():
        """Opens the text file in the system's default text editor."""
        file_path="logs.txt"
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{file_path}'")
        else:  # Linux and other Unix-like systems
            os.system(f"xdg-open '{file_path}'")
    open_button = ctk.CTkButton(
        logframe, 
        text="Open Log File",
        command=lambda:open_text_file(),        
        text_color="black",
        fg_color="#ffd700", 
        hover_color="#4c5375",
        corner_radius=10,
        height=50,
        width=250
    )
    open_button.place(x=295,y=350)

    text_box = scrolledtext.ScrolledText(logframe, wrap=tk.WORD, width=100, height=20)
    text_box.pack(padx=10, pady=10)
    
    graph_button.place(x=295,y=330)
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.resizable(False, False)
    updatetime()
    updateapp()
    window.mainloop()
        


import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading


class ChatClient:
    #main screen
    def __init__(self, master:tk.Tk):
        self.answer_count = 1  #which question are we answering
        self.question_active = False #are there any qquestion on screen now?
        self.master = master 
        master.title("Welcome to SuQuiz!") #main screen title
        master.grid_columnconfigure(0, weight=3)  #left col
        master.grid_columnconfigure(1, weight=1)  #right col

        master.grid_rowconfigure(index=list(range(4)), weight=1) #makes bigger screen

        self.client_socket = None #server connection
        self.is_connected = False #server conn status , connected or not
        self.thread = None #receive thread

        self.create_widgets() #gui elements come here

    def create_widgets(self):
        # Connection frame
        conn_frame = tk.Frame(self.master) 
        conn_frame.grid(row=0,column=0, columnspan=6, pady=10, padx=10, sticky="NWSE")
        
        conn_frame.grid_columnconfigure(index=list(range(6)), weight=1)
        conn_frame.grid_rowconfigure(index=0, weight=1)

        #for ip entry
        tk.Label(conn_frame, text="IP:").grid(row=0,column=0)
        self.ip_entry = tk.Entry(conn_frame)
        self.ip_entry.grid(row=0,column=1)

#for port entry
        tk.Label(conn_frame, text="Port:").grid(row=0,column=2)
        self.port_entry = tk.Entry(conn_frame)
        self.port_entry.grid(row=0,column=3)
#for username entry
        tk.Label(conn_frame, text="Username:").grid(row=0,column=4)
        self.name_entry = tk.Entry(conn_frame)
        self.name_entry.grid(row=0,column=5)

        #enter game and disconnect button
        self.connect_button = tk.Button(self.master, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=1,column=0, columnspan=5)

        # Message display
        self.text_widget = tk.Text(self.master, width = 55 , height = 30, state= tk.DISABLED)
        self.text_widget.grid(row=2,column=0, pady=10, padx=10, sticky="NSEW")
#question place
        self.question_place = tk.Label(self.master, text = " ")
        self.question_place.grid(row= 2, column = 1, padx= 10 , pady=10, sticky ="NW" )
#answers place
        self.answers()
        self.a.config(state =tk.DISABLED)
        self.b.config(state =tk.DISABLED)
        self.c.config(state =tk.DISABLED)
#submit button will be diasbled if there is no question
        self.submit_button.config(state =tk.DISABLED)

#used in connect disconnect button to act accordingly
    def toggle_connection(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
#to connect server
    def connect(self):
        #if already connected
        if self.is_connected:
            return 
        
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get()
        name = self.name_entry.get()

         #to control are any empty place in entries
        if not ip or not port_str or not name:
            messagebox.showerror("Error", "All fields must be filled out.")
            return
        
        #very basic ip control just based on . 
        if ip.count(".") != 3:
            messagebox.showerror("Error" ,"Invalid IP address.")
            return
    

        try:
            #try connection to server
            port = int(port_str)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
     
        
        except Exception:
            #if there is an error to connect to server
            messagebox.showerror("Connection Error." ,"Could not connect")
            self.is_connected = False
            #close the socket
            if self.client_socket:
                self.client_socket.close()
            return
        #if connected to server 
        self.is_connected = True
        self.client_socket.sendall(name.encode()) #send username to server

#we dont want to change port ip username during connection. so they are disabled
        self.ip_entry.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)
        self.name_entry.config(state=tk.DISABLED)

#receive thread, get messages from server
        self.thread = threading.Thread(
            target=self.receive_messages,daemon=True )
        self.thread.start()

        self.add_message_to_text(f"*** Connected to {ip}:{port} *** ")
        self.connect_button.config(text="Disconnect")


            
    def disconnect(self):
        #if not connected, do nothing
        if not self.is_connected:
            return

#in case we connected, disconnected and connected again
        self.is_connected = False
        self.question_active = False
        self.answer_count = 1

        try: #if socket is already closed
            self.client_socket.close() 
        except Exception as e:
           print("Socket close error:", e)

        try:
            self.client_socket.close()
        except Exception as e:
           print("Socket close error:", e)

#open connection after disconn so a client can connect again
        self.client_socket = None   

        self.connect_button.config(text="Connect")
        self.ip_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.name_entry.config(state=tk.NORMAL)
        self.add_message_to_text("*** Disconnected *** ")
#diasble answer part bcs we are disconnected
        self.a.config(state=tk.DISABLED)
        self.b.config(state=tk.DISABLED)
        self.c.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)



    def add_message_to_text(self, message):
        self.master.after(0, self.add_message, message)

    def add_message(self, message):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + "\n")
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.see(tk.END)


    def receive_messages(self):
        empty = ""
        while self.is_connected and self.client_socket:
            try:
                msg = self.client_socket.recv(1024).decode() #receive messages
                if not msg: #if server closed any case
                    self.master.after(0, self.disconnect)
                    break #close
                
                empty = empty + msg  #to write and add messages
                while ("\n" in empty): #to seperate messages line line 
                    line, empty = empty.split("\n", 1)
                    self.master.after(0, self.handle_message, line.strip())

#conn error
            except (socket.error, OSError):
                self.master.after(0, self.disconnect)
                break #close
 #the func that we understand messages   
    def handle_message(self, msg):
            parts = msg.split("|")
            header = parts[0].strip()
#the server will send messages with headers like question chat or vs vs
    
            if header == "QUESTION":
                self.question_place.config(text=parts[1])
                self.a.config(text=parts[2]) #opt a
                self.b.config(text=parts[3]) #opt b
                self.c.config(text=parts[4]) #opt c
#choose answer from radio buttons
                self.question_active = True
                self.a.config(state=tk.NORMAL)
                self.b.config(state=tk.NORMAL)
                self.c.config(state=tk.NORMAL)
                self.submit_button.config(state=tk.NORMAL)

            elif header == "CHAT":
                sender = parts[1]
                content = parts[2]
                self.add_message_to_text(f"{sender}: {content}")

         
            elif header == "INFO":
                self.add_message_to_text(f"[INFO] {parts[1]}")

 #the server will calculate points      
            elif header == "SCORE_INIT":
                scoreboard = parts[1]
                self.add_message_to_text(f"Initial scoreboard: {scoreboard}")

        
            elif header == "ROUND_SUMMARY":
                correct = parts[1]
                first = parts[2]
                scoreboard = parts[3]

                self.add_message_to_text(
                    f"Round summary: Correct = {correct}, FirstCorrect = {first}, Scoreboard = {scoreboard}"
                )

    
            elif header == "ROUND_PERSONAL ":
                yourName = parts[1]
                yourAnswer = parts[2]
                isCorrect = parts[3]
                isFirst = parts[4]
                earned = parts[5]
                correct = parts[6]
                scoreboard = parts[7]

                if isCorrect == "1":
                    self.add_message_to_text(
                        f"You answered {yourAnswer} -> CORRECT (+{earned})"
                    )
                else:
                    self.add_message_to_text(
                        f"You answered {yourAnswer} -> WRONG, earned 0. Correct was {correct}"
                    )

                if isFirst == "1":
                    self.add_message_to_text(
                        "You were the first correct (+extra points)."
                    )

                self.add_message_to_text(f"Scoreboard: {scoreboard}")

          
            elif header == "FINAL":
                ranking = parts[1]
                winners = parts[2]
                scoreboard = parts[3]

                self.add_message_to_text("***GAME OVER***")
                self.add_message_to_text(f" *** Winners: {winners}")
                self.add_message_to_text(f" **** Final Ranking: {ranking}")
                self.add_message_to_text(f" ****** Final Scoreboard: {scoreboard}")

            
                self.question_active = False
                self.a.config(state=tk.DISABLED)
                self.b.config(state=tk.DISABLED)
                self.c.config(state=tk.DISABLED)
                self.submit_button.config(state=tk.DISABLED)

    
            elif header == "REJECT":
                self.add_message_to_text(f"[REJECT] {parts[1]}")
        

    #a b c radio buttons, taken from example4.py lab notes
    def submit(self):
        if not self.is_connected or not self.question_active:
            return
        answer = self.answer_var.get()
        self.add_message_to_text(f"{self.answer_count}. given answer: {answer}")
        self.answer_count += 1

        self.client_socket.sendall(f"{answer}\n".encode())


        self.question_active = False
        self.a.config(state=tk.DISABLED)
        self.b.config(state=tk.DISABLED)
        self.c.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)


    
    #answer options
    def answers(self):
        self.answer_var = tk.StringVar(value = "A")
        self.answer_frame = tk.LabelFrame(self.master)
        self.answer_frame.grid(row= 2, column = 1, padx = 10, pady = 60, sticky= "NW")

        self.a = tk.Radiobutton(self.answer_frame,  variable=self.answer_var, value="A")
        self.a.grid(row=0, column=0, sticky="w")

        self.b = tk.Radiobutton(self.answer_frame,variable=self.answer_var, value="B")
        self.b.grid(row=1, column=0, sticky="w")

        self.c = tk.Radiobutton(self.answer_frame,variable=self.answer_var, value="C")
        self.c.grid(row=2, column=0, sticky="w")

        #call submit button function
        self.submit_button = tk.Button(self.answer_frame, text="Submit Answer", command=self.submit)
        self.submit_button.grid(row=3, column=0, pady=5)


#start program
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()

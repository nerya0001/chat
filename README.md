# RUDP Chat app

> Made by Nerya Bigon and Eitan shenkolovski
* Assignment in networking course    

In this assignment we were requiered to develop a chat application in tow parts.  
1. basic messaging over TCP.
2. The abilty to transfer files over RUDP (realiable UDP).  
3. every thing is managed in SQLITE database - users, files, messages.
4. we've also created a GUI interface for the client, but due to the fact that it does not fully operational as of yet, we'll only demonstrate it in person.

Essentially we we had to implement reliable file transfer by implementing something similar to how TCP works.  
 
* [how to run](https://github.com/nerya0001/chat/blob/main/README.md#how-to-use)   
* [video of the operation](https://youtu.be/sDj64U_8Os4) 
* [GUI screenshots](https://github.com/nerya0001/chat/blob/main/README.md#gui-screenshots)  
* [video of the gui](https://youtu.be/PFcUYh2-zNc) 



## The algorithm
for the reliable UDP we chose to implement something close to selective repeat congestion control.   
in addition we use flow control that is similar to cubic algorithm.    
1.	Client send file request to the server.
2.	establish three way handshake over UDP.
3.	start with windows size 3, load pockets into the window and send them.
4.	wait for ACKs 
5.	The algorithm will resend any pockets that didn't received ACK.
6.	after all the packets in the window received ACK we increase the size of the window by two (slow start) only until half of the last maximum.
7.	Using flow control to increase and decrease the window size in the event of duplicate ACK we decrease the window size by half and continuing sending the packets.
8.	In the event of a timeout we consider this as very serious event and decrease window size to one, and start a slow start all over again.  

![Picture2](https://user-images.githubusercontent.com/66886354/156899228-b1ed5e38-2cfe-40e0-93ab-9f85139f5fcc.png)



## UML
![UML](https://user-images.githubusercontent.com/66886354/156899067-df696232-1673-4c61-8b41-e4f5d85ab34b.png)


## Pcap and screenshots:  

![image](https://user-images.githubusercontent.com/66886354/156899379-7b6d0d48-3d48-4146-bf69-9b8735f6a0a7.png)  

in the folowing screnshot we can see the handshake between the server and the client, and we can see the window get bigger - by the fact the more packet are beening loaded:  

![image](https://user-images.githubusercontent.com/66886354/156899444-25bb99e2-c25a-48d3-bd36-0a96668836f4.png)  

and in the end the last packet and the closing of the connection:  

![image](https://user-images.githubusercontent.com/66886354/156899396-1652f9a9-de6f-4509-95b8-78ad8c356d51.png)  

here we can see the handshake that we successfuly capture with wireshark:  

![image](https://user-images.githubusercontent.com/66886354/156899543-80a9e45b-89b9-4b65-9fcc-1a4ff059a645.png)  

![image](https://user-images.githubusercontent.com/66886354/156899548-8a2915fe-5e73-49fe-b849-1f774a38fee0.png)  

here we capture DUP ACK:  

![image](https://user-images.githubusercontent.com/66886354/156899566-7267f0b4-1bdc-488e-abe6-c1d7fd9bf3c8.png)  

and finely we captured the FIN message that tell as we got the last packet  

![image](https://user-images.githubusercontent.com/66886354/156899600-972f2ba9-8f3c-4d70-9e9b-c93544b1232f.png)  



## How To Run

download this repository and folow this steps:
* very important to make sure tha the correct IP addresses are in both the server file and in the client file.
* make sure that the files `hello.txt`, `lama.png`, `mov.mp4` are in the same folder as the `server.py`.
* in order of not getting in truble, if you want to activate a client in another pc, take all of the files with you,  
also it is only neseccery that you have the `client.py`, and the `util`, for the off chance that we forgot somthing like an import of some kind.  


1. open a terminal window in the folder with the `server.py` file.
2. run the folowing comand:  

```
python3 server.py
```

3. open a second terminal window, in the same folder as the `client.py` file.
4. run the folowing comand:  

```
python3 client.py
```

5. since we used a database, you first have to register or else you wont be able to login.
6. folow the prompt that show up.
7. after you successfuly loged in you can send messages freely, and run the folowing comands:    
8. you can open as many client as you want.

to get the registered clients:
```
/clientslist
```
to get the online clients:
```
/online
```
to get the available files:
```
/fileslist
```
to download a file:
```
/file filename
```
to send private message:
```
/to username
```    

![image](https://user-images.githubusercontent.com/66886354/156899335-abdb48e6-9e49-43d4-9f5f-89a7779b32e8.png)   


## GUI screenshots
![image](https://user-images.githubusercontent.com/66886354/156900289-49f7f832-a01a-441e-9d2e-b0446e28ec98.png)
![image](https://user-images.githubusercontent.com/66886354/156900303-c6d3e8ca-84e2-42c7-b7de-c1587c6f1358.png)
![image](https://user-images.githubusercontent.com/66886354/156900334-0738b899-4971-44ad-a597-0d186f38a263.png)


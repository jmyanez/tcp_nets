# nets-tcp-file-transfer

For this lab, you must define a file transfer protocol and implement a client and server.  The server must be 
* single-threaded, 
* and accept multiple concurrent client connections.   

Like the demo code provided for this course, your code 
* should be structured around a single loop with a single call to select(), 
* and all information about protocol state should be explicitly stored in variables 

Recall that unlike UDP, which is a message-oriented protocol, TCP is stream-oriented.  

A practical implication of this difference is that the outputs of multiple writes may be concatenated and reads may only return a portion of the data already sent.  You are strongly encouraged to test your implementation using the stammering proxy from https://github.com/robustUTEP/nets-tcp-proxy.git


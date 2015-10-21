
To deploy the server, you need a linux user that can ssh in with a key and can sudo without password prompt:

    mkdir .ssh
    nano authorized_keys

    sudo visudo
    vrkroot ALL=(ALL) NOPASSWD: ALL

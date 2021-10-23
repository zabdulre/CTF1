#!/bin/bash

sudo ufw disable

sudo ufw reset

sudo ufw default deny incoming

sudo ufw allow out 80/tcp
sudo ufw allow in 80/tcp 

sudo ufw allow out 3306
sudo ufw allow in 3306

sudo ufw allow out 22
sudo ufw allow in 22

sudo ufw allow out 111
sudo ufw allow in 111

sudo ufw allow out 16505
sudo ufw allow in 16505

sudo ufw enable




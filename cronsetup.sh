sudo nmap -p- localhost | grep open | awk '{print $1}' | grep -E -v '3306|111|22|16505' | grep -o '[0-9]*' | xargs -n1 -I% sudo lsof -t -i:% | xargs -n1 sudo kill -9 
echo "did cron \n" >> cronlog.txt
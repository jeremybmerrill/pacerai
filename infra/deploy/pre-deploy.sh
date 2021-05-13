
# Remove if previous deployment folder exists
rm -rf /home/ubuntu/prevdeploy-tow-pacer

# Backup current deployment 
mv /home/ubuntu/tow-pacer /home/ubuntu/prevdeploy-tow-pacer

mkdir /home/ubuntu/tow-pacer

chown ubuntu:ubuntu /home/ubuntu/tow-pacer

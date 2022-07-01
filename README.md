# unity-nfs-checker
* for each dir in dir_list, time how long it takes to `ls`
* do this once every loop_wait_time_s seconds
* if any of these times are greater than min_report_time_s, add a line to the report queue
* if there's anything in the queue,
    * and it's been more than max_email_frequency_min since the last email,
    *     and email is enabled in the config
  * send an email containing the report queue, and clear the queue.

# sample config file
```
# nfs_checker_config.ini contains a cleartext password
#     should be excluded from source control!
#     should not be readable by any other user!
[email]
enabled = True
to = hpc@it.umass.edu
from = hpc@it.umass.edu
signature = best, nfs_checker
smtp_server = mailhub.oit.umass.edu
smtp_port = 465
smtp_user = admin
smtp_password = password
smtp_is_ssl = True
max_email_frequency_min = 30

[logger]
info_filename = /opt/logs/nfs_checker.log
error_filename = /opt/logs/nfs_checker_error.log
max_filesize_megabytes = 100
backup_count = 1

[misc]
dir_list = 
        /scratch,
        /project,
        /home,
        /work
min_report_time_s = 0.25
loop_wait_time_s = 10

```

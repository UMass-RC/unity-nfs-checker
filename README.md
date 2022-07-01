# unity-nfs-checker
* for each dir in dir_list, time how long it takes to `ls`
* do this once every loop_wait_time_s seconds
* if any of these times are greater than min_report_time_s, add a line to the report queue
* if there's anything in the queue,
    * and it's been more than max_email_frequency_min since the last email,
    *     and email is enabled in the config
  * send an email containing the report queue, and clear the queue.

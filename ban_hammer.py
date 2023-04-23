import time

class Action:
    block_local = "BLOCK_LOCAL"
    report_central = "REPORT_CENTRAL"
    record_local = "RECORD_LOCAL"

class BanHammer:
    def __init__(self, bans, return_rates=False):
        # Here I would modify and sort the bans by threshold window, limit DESC.
        # self.bans = custom_sort(bans)

        self.bans = bans
        self.return_rates = return_rates
        self.blocked = {}
        self.metrics = {}
        self.stats = {}

    def __current_time(self):
        return time.time()
    
    def collect_stats(self, metric):
        if metric not in self.stats:
            self.stats[metric] = []

        self.stats[metric].append(self.__current_time())

    def incr(self, token, metric):
        if self.return_rates:
            self.collect_stats(metric=metric)

        if self.token_is_blocked(token):
            passed = False
        else:
            # If token doesn't exist, initialize a new dictionary for it
            if token not in self.metrics:
                self.metrics[token] = {}

            # Initialize a dictionary for the token in the metric dictionary if it doesn't exist
            if metric not in self.metrics[token]:
                self.metrics[token][metric] = []

            # Add the current timestamp to the token's list of timestamps for this metric
            self.metrics[token][metric].append(self.__current_time())

            # Get the configuration for this metric from the bans dictionary
            config = self.bans[metric]["thresholds"]
            # Check if any of the thresholds have been reached for this metric and token
            passed = True
            for threshold in config:
                if self.threshold_reached(token, metric, threshold):
                    if Action.block_local in threshold["action"]:
                        self.blocked[token] = self.__current_time() + threshold["action_duration"]
                    if Action.report_central in threshold["action"]:
                        self.report_to_central(token)
                    if Action.record_local in threshold["action"]:
                        self.record_local(token, metric)
                    passed = False

        # Return a tuple indicating whether the token should be blocked and the current stats if return_rates is True
        if self.return_rates:
            return passed, self.status_all(metric)
        else:
            return passed
        
    def token_is_blocked(self, token):
        if token in self.blocked:
            if self.blocked[token] - self.__current_time() > 0:
                return True
            else:
                self.unblock_token(token)
                return False
        else:
            return False
    
    def unblock_token(self, token):
        del self.blocked[token]

    def threshold_reached(self, token, metric, threshold):
        # Get the timestamps for this token and metric
        # As a next step improvement we can delete all the data less than timestamps[timestamps_len - threshold["limit"]] index
        timestamps = self.metrics[token][metric]
        timestamps_len = len(timestamps)
        return len(timestamps) >= threshold["limit"] and \
            timestamps[timestamps_len - 1] - timestamps[timestamps_len - threshold["limit"]] <= threshold["window"]

    def report_to_central(self, token):
        print(f"Reporting {token} to central server...")

    def record_local(self, token, metric):
        print(f"Recording {metric} for {token} locally...")

    def status_all(self, specific_metric=None):
        # Define a dictionary to store the bucket counts for each metric
        bucket_counts = {}

        # Loop through each metric and its corresponding epoch times in the dictionary
        if specific_metric:
            return self.__generate_stat(metric=specific_metric, epoch_times=self.stats[specific_metric])
        else:
            for metric, epoch_times in self.stats.items():
                # Initialize the bucket counts for the current metric to 0
                bucket_counts[metric] = self.__generate_stat(metric=metric, epoch_times=epoch_times)

        return bucket_counts
    
    def __generate_stat(self, metric, epoch_times):
        bucket_intervals = {
            '1m': 60,
            '10m': 600,
            '60m': 3600
        }
       
        # Initialize the bucket counts for the current metric to 0
        metric = {
            'token_rate_1m': 0,
            'token_rate_10m': 0,
            'token_rate_60m': 0
        }

        # Loop through each epoch time for the current metric
        for epoch_time in epoch_times:
            # Calculate the time difference (in seconds) between the current time and the epoch time
            time_difference = self.__current_time() - epoch_time

            # Loop through each bucket interval and increment the corresponding bucket count if the time difference falls into that bucket
            for bucket_name, bucket_interval in bucket_intervals.items():
                if time_difference <= bucket_interval:
                    metric[f'token_rate_{bucket_name}'] += 1

        return metric

        
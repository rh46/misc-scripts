#!/usr/bin/python
import sys, json, boto3, re

#### Configuration Section: Start ################

#### aws profiles
profiles = [] ## defined profiles in ~/.aws/credentials

#### Configuration Section: End ################


def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts


def search_aws(name,is_ip):
    aws_systems = {}   ## create empty dictionary
    for profile in profiles:    ## loop through profiles
        session = boto3.session.Session(profile_name=profile)   ## new session using current profile from loop
        boto3.setup_default_session(profile_name=profile)       ## make new session the default session
        ec2 = boto3.resource('ec2') ## create ec2 client using default session
        aws_account_id = boto3.client('sts').get_caller_identity()['Account']   ## get aws account id
        #aws_account_alias = boto3.client('organizations').describe_account(AccountId=aws_account_id).get('Account').get('Name')    ## DISABLED: need to handle permissions error on DescribeAccount
        if is_ip:   ## hostname is decoded to ip address
            instances = ec2.instances.filter(
                Filters=[{'Name': 'private-ip-address', 'Values': [name]}])   ## search for given ip address
        else:
            instances = ec2.instances.filter(
                Filters=[{'Name': 'tag:Name', 'Values': [name]}])   ## search hostname as tag
        for instance in instances:
            aws_tuple = (aws_account_id, instance.id)  ## create tuple to store instance and account info
            #aws_tuple = (aws_account_id, aws_account_alias, instance.id)  ## DISABLED: need to handle permissions error on DescribeAccount
            aws_systems[name] = aws_tuple ## add each instance to dictionary using id as key and aws_tuple as value
    return aws_systems


def main():
    # check configuration
    if len(profiles) == 0:
        print "Error: no aws profiles defined in Configuration Section"
        sys.exit()

    args = sys.argv[1:]

    if not args:
        print 'usage:', sys.argv[0],'<hostname>'
        sys.exit(1)

    for arg in args:
        match = re.search(r'(?i)ip-\w{8}', arg)   ## regex search if argument is a hex encoded hostname

        if match:   ## if match is found
            is_ip = True
            name = "%i.%i.%i.%i" % (int(arg[3:5],16),int(arg[5:7],16),int(arg[7:9],16),int(arg[9:11],16)) ## convert hex to ip address
        else:
            is_ip = False
            name = arg

        aws_results = search_aws(name, is_ip)   ## call search_aws for passed arg
        for key in aws_results:
            print arg, "found in AWS account id:", aws_results[key][0], "instance_id:", aws_results[key][1]
            #print arg, "found in AWS account id:", aws_results[key][0]+" ("+aws_results[key][1]+")", "instance_id:", aws_results[key][2]        ## DISABLED: need to handle permissions error on DescribeAccount


if __name__ == '__main__':
    main()

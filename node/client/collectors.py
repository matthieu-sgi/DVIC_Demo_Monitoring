import subprocess

def get_machine_hardware_info():
    # Get system temperature
    counter = 0
    data = {}

    # Machine name 
    with open('/etc/hostname', 'r') as f:
        data["machine_name"] = f.read().strip()
    
    #FIXME Machine IP address ## Has to be fixed, only display the local IP address
    with open('/etc/hosts', 'r') as f:
        data["machine_ip"] = f.read().split()[0]


    temps = {}
    while True :
        try:
            temp_name = ''
            temp_temp = 0
            with open(f'/sys/class/thermal/thermal_zone{counter}/type', 'r') as type_file:
                temp_name = type_file.read().strip()
            with open(f'/sys/class/thermal/thermal_zone{counter}/temp', 'r') as temp_file:
                temp_temp = float(temp_file.read()) / 1000
            temps[temp_name] = temp_temp
            counter += 1
        except FileNotFoundError:
            break
    data["temperature"] = temps
    
    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    cpu_usage = round(100 * (1.0 - (float)(idle / total)), 2)
    data["cpu_usage"] = cpu_usage

    # Get system memory
    with open('/proc/meminfo') as f:
        meminfo = dict((i.split()[0].rstrip(':'), int(i.split()[1])) for i in f.readlines())
    mem_total = meminfo['MemTotal']
    mem_free = meminfo['MemFree']
    mem_available = meminfo['MemAvailable']
    mem_used = round(100 * (1.0 - (float)(mem_available / mem_total)), 2)
    memory_info = {
        'total': mem_total,
        'free': mem_free,
        'available': mem_available,
        'used': mem_used
    }
    data["memory_info"] = memory_info
    return data

def get_machine_software_info():
    '''Get the software information of the DVIC node (demo proc IsAlive).'''

    # Fetch the state of the demo process
    stdout, stderr = None, None
    with subprocess.Popen('ps -A | grep demo', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        stdout, stderr = process.communicate()

    #TODO : Check if the demo process is running, return the state of the demo process (IS_ALIVE, IS_DEAD, IS_NOT_RUNNING)
    
    return [stdout.decode('utf-8'), stderr.decode('utf-8')]

    
def get_demo_logs():
    '''Get the logs of the demo process.'''
    # Verify if the fifo file exists
    if not os.path.exists('/tmp/dvic_log_fifo'):
        return self.create_json_message('demo_logs_response', {'logs': 'No logs available.'})


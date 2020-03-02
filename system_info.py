# -*-coding:utf-8-*-


import os
import time
import psutil
import socket
import netifaces
import ctypes
import pynvml


class MyCPU(object):
    def __init__(self):
        super(MyCPU, self).__init__()
        self.cpu_basic_info = None
        self.cpu_id_c = None
        self.cpu_id_python = None
        self.physical_cpu_count = None
        self.logical_cpu_count = None

    def get_cpu_basic_info(self):
        '''
        获得CPU的品牌、型号、频率、物理核数、逻辑核数
        :return:
        '''
        command = "cat /proc/cpuinfo|grep 'model name'"
        result = os.popen(command).readline().split()
        self.cpu_basic_info = ' '.join(result[3:])
        self.physical_cpu_count = psutil.cpu_count(logical=False)
        self.logical_cpu_count = psutil.cpu_count()

    def get_cpu_id_by_c(self):
        '''
        通过调用C库来读取CPU的序列号，执行gcc -shared -Wl,-soname,cpu_info -o cpu_info.so -fPIC get_cpu_info.c命令
        来生成cpu_info.so文件，然后就可以在Python中读取CPU的序列号
        :return:
        '''
        buf = ctypes.create_string_buffer('hello'.encode('gbk'), 17)
        cpu = ctypes.CDLL('./cpu_info.so')
        cpu.cpu_id(buf)
        CPU_ID_bytes = buf.value
        CPU_ID_str = CPU_ID_bytes.decode('utf-8')
        self.cpu_id_c = CPU_ID_str

    def get_cpu_id_by_python(self):
        '''
        获得CPU的序列号
        :return:
        '''
        sudoPassword = 'password'
        command = 'sudo dmidecode -t 4 | grep ID'
        result = os.popen('echo %s|sudo -S %s'%(sudoPassword, command)).read()
        result = result.strip().replace(' ', '')[3:]
        self.cpu_id_python = result

    def get_cpu_usage_rate(self, interval=1, percpu=False):
        '''
        获取CPU的使用率
        :param interval: 指定的是计算CPU使用率的时间间隔
        :param percpu: 如果是False返回的是总的CPU使用率，如果是True返回的是每一个CPU的使用率
        :return:
        '''
        return psutil.cpu_percent(interval=interval, percpu=percpu)

    def get_cpu_temper(self, type='Core'):
        '''
        获取CPU的温度
        :param type: 使用默认值即可
        :return:
        '''
        temps = psutil.sensors_temperatures()
        dict_cpu_temp = {}
        if 'coretemp' in temps:
            for entry in temps['coretemp']:
                if type in entry.label:
                    dict_cpu_temp[entry.label] = entry.current
        else:
            return {}
        return dict_cpu_temp

class MyMem(object):
    def __init__(self):
        super(MyMem, self).__init__()
        self.mem_total = None
        self.mem_available = None

    def get_mem_info(self):
        '''
        内存的总容量和可用容量
        :return:
        '''
        command1 = "cat /proc/meminfo|grep 'MemTotal'"
        command2 = "cat /proc/meminfo|grep 'MemAvailable'"
        self.mem_total = int(os.popen(command1).read().split()[1])
        self.mem_available = int(os.popen(command2).read().split()[1])

    def get_all_mem_info(self):
        '''
        内存容量的计算在系统中是按照1024换算的
        :return:
        '''
        mem = psutil.virtual_memory()
        total_mem = float(mem.total) / 1024
        available_mem = float(mem.available) / 1024
        used_mem = float(mem.used) / 1024
        free_mem = float(mem.free) / 1024
        return {'total': total_mem,
                'available': available_mem,
                'used': used_mem,
                'free': free_mem}

    def get_mem_usage_rate1(self):
        '''
        通过psutil模块获取内存使用率
        :return:
        '''
        return psutil.virtual_memory().percent

    def get_mem_usage_rate2(self):
        '''
        通过free命令计算内存的使用率，经过验证获取内存使用率的这两个方法得到的结果基本是一致的
        :return:
        '''
        command = 'free'
        result = os.popen(command).readlines()
        result = result[1].split()
        mem_total = float(result[1])
        mem_available = float(result[6])
        mem_usage_rate = (1 - mem_available / mem_total) * 100
        return mem_usage_rate

class MyDisk(object):
    def __init__(self):
        super(MyDisk, self).__init__()
        self.all_disk_info = None
        self.total_capacity = 0.0
        self.used_capacity = 0.0
        self.free_capacity = 0.0
        self.percent = 0.0

    def get_all_disk_info(self, all=False):
        '''
        系统硬盘总容量、已使用容量、未使用容量、使用率
        :param all:
        :return:
        '''
        self.all_disk_info = psutil.disk_partitions(all=all)
        for disk in self.all_disk_info:
            info_dict = self.get_one_disk_info(disk.mountpoint)
            self.total_capacity += info_dict['total']
            self.used_capacity += info_dict['used']
            self.free_capacity += info_dict['free']
        self.percent = self.used_capacity / self.total_capacity * 100.0

    def get_one_disk_info(self, mount_point):
        '''
        获得某一块硬盘或者某一个挂载点的存储信息，硬盘容量的计算在系统中是按照1000换算的
        :param mount_point: 挂载点路径
        :return: 总容量，使用容量，未使用容量，使用容量的百分比
        '''
        one_disk_info = psutil.disk_usage(mount_point)
        return {'total': float(one_disk_info.total) / 1e9,
                'used': float(one_disk_info.used) / 1e9,
                'free': float(one_disk_info.free) / 1e9,
                'percent': one_disk_info.percent}

class MySystem(object):
    def __init__(self):
        super(MySystem, self).__init__()
        self.routingGateway = None
        self.routingNicName = None
        self.routingNicMacAddr = None
        self.routingIPAddr = None
        self.routingNetmask = None
        self.boot_time = None
        self.system_sn = None
        self.baseboard_sn = None

    def get_ip(self):
        '''
        获取内网IP地址
        :return:
        '''
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def get_network_info(self):
        # 获得所有真实的网卡和网关
        gateways = netifaces.gateways()
        # 获得当前正在使用的网卡和网关
        self.routingGateway, self.routingNicName = gateways['default'][netifaces.AF_INET]
        # 获得所有的网卡
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            if interface == self.routingNicName:
                ifaddresses = netifaces.ifaddresses(interface)
                self.routingNicMacAddr = ifaddresses[netifaces.AF_LINK][0]['addr']
                self.routingIPAddr = ifaddresses[netifaces.AF_INET][0]['addr']
                self.routingNetmask = ifaddresses[netifaces.AF_INET][0]['netmask']

    def get_boot_time(self):
        '''
        获得系统的开机时间，除了下面的方式外，下面这个命令也可以获得系统开机时间
        date -d "$(awk -F. '{print $1}' /proc/uptime) second ago" +"%Y-%m-%d %H:%M:%S"
        :return:
        '''
        self.boot_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(psutil.boot_time()))

    def get_run_time(self):
        '''
        获得系统从开机到当前的运行时间
        :return:
        '''
        command = 'cat /proc/uptime'
        runtime_sec = float(os.popen(command).readline().split()[0])
        runtime_hour = runtime_sec / 3600
        return runtime_sec, runtime_hour

    def get_all_users(self):
        '''
        获得当前登录系统的所有用户的信息
        :return:
        '''
        all_users = psutil.users()
        return all_users

    def get_all_processes_info(self):
        '''
        获得所有进程对象，通过每一个对象获得单个进程的信息
        :return:
        '''
        all_processes = psutil.process_iter()
        return all_processes

    def get_all_PID(self):
        '''
        获得系统中所有的PID
        :return:
        '''
        pids = psutil.pids()
        return pids

    def get_one_process_info(self, pid):
        '''
        获得单个进程的信息
        :param pid:
        :return:
        '''
        p = psutil.Process(pid)
        return {'name': p.name(),
                'status': p.status(),
                'create_time': p.create_time(),
                'memory_percent': p.memory_percent(),
                'num_threads': p.num_threads()}

    def get_system_sn(self):
        '''
        获得系统的序列号
        :return:
        '''
        sudoPassword = 'password'
        command = "sudo dmidecode -q --type system|grep 'Serial Number'"
        self.system_sn = os.popen('echo %s|sudo -S %s'%(sudoPassword, command)).readline().split()[2]

    def get_baseboard_sn(self):
        '''
        获取主板的序列号
        :return:
        '''
        sudoPassword = 'password'
        command = "sudo dmidecode -q --type baseboard|grep 'Serial Number'"
        self.baseboard_sn = os.popen('echo %s|sudo -S %s'%(sudoPassword, command)).readline().split()[2]

class MyGPU(object):
    def __init__(self):
        super(MyGPU, self).__init__()
        pynvml.nvmlInit()
        self.cuda_version = None
        self.cudnn_version = None
        self.driver_version = None
        self.all_gpu_model = {}

    def get_all_gpu_model(self):
        '''
        获得所有GPU的型号
        :return:
        '''
        command = 'lspci|grep -i vga'
        result = os.popen(command).readlines()
        idx = 0
        for item in result:
            self.all_gpu_model['GPU'+str(idx)] = item.split(':')[-1].strip()
            idx += 1

    def get_gpu_driver_version(self):
        '''
        获得显卡驱动的版本
        :return:
        '''
        driver = 'cat /proc/driver/nvidia/version|grep "NVRM"'
        self.driver_version = os.popen(driver).read().split()[7]

    def get_cuda_cudnn_info(self):
        '''
        获得cuda和cudnn的版本
        :return:
        '''
        cuda = 'cat /usr/local/cuda/version.txt'
        cudnn = 'cat /usr/local/cuda/include/cudnn.h | grep "#define CUDNN_MAJOR" -A 2'
        self.cuda_version = os.popen(cuda).readline().split()[2]
        result = os.popen(cudnn).readlines()
        version_list = []
        for item in result:
            version_list.append(item.split()[2])
        self.cudnn_version = 'v' + '.'.join(version_list)

    def get_nvidia_gpu_driver_version(self):
        '''
        获得显卡驱动的版本
        :return:
        '''
        return pynvml.nvmlSystemGetDriverVersion().decode('utf-8')

    def get_nvidia_gpu_info(self):
        '''
        获得英伟达GPU的信息
        :return:
        '''
        info_dict = {}
        device_count = pynvml.nvmlDeviceGetCount()
        info_dict['device_count'] = device_count
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            info_dict['handle'+str(i)] = handle
            info_dict['GPU'+str(i)] = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
        return info_dict

    def get_nvidia_gpu_mem_info(self, handle):
        '''
        获得英伟达GPU的显存信息
        :param handle:
        :return:
        '''
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return {'gpu_mem_total': mem_info.total,
                'gpu_mem_used': mem_info.used,
                'gpu_mem_free': mem_info.free,
                'usage_rate': mem_info.used / mem_info.total * 100}

    def get_nvidia_gpu_temper(self, handle, sensor=0):
        '''
        获得英伟达GPU的温度
        :param handle:
        :param sensor:
        :return:
        '''
        temper = pynvml.nvmlDeviceGetTemperature(handle, sensor)
        return temper

    def close_pynvml(self):
        '''
        关闭pynvml工具
        :return:
        '''
        pynvml.nvmlShutdown()

    def get_all_info(self):
        command = 'gpustat -cpu'
        result = os.popen(command).readlines()
        for item in result:
            print(item)


if __name__ == '__main__':
    mycpu = MyCPU()
    mymem = MyMem()
    mydisk = MyDisk()
    mysys = MySystem()
    mygpu = MyGPU()
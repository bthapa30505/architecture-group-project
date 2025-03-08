import m5
from m5.objects import *

# These are the caches available for the smartwatch architecture
class L1_ICache(Cache):
    size = '32kB'
    assoc = 4
    tag_latency = 10
    data_latency = 10
    response_latency = 10
    mshrs = 10
    tgts_per_mshr = 8

class L1_DCache(Cache):
    size = '32kB'
    assoc = 4
    tag_latency = 10
    data_latency = 10
    response_latency = 10
    mshrs = 10
    tgts_per_mshr = 8

class L2Cache(Cache):
    size = '256kB'
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

# Define system
system = System()

# Set up voltage and frequency domains (for DVFS)
system.voltage_domain = VoltageDomain()
system.clk_domain = SrcClockDomain()
system.clk_domain.voltage_domain = system.voltage_domain
system.clk_domain.clock = '2GHz'  # Default frequency

# Define a lower power clock domain
system.low_power_clk_domain = SrcClockDomain()
system.low_power_clk_domain.voltage_domain = system.voltage_domain
system.low_power_clk_domain.clock = '1GHz'  # Lower power frequency

# O3CPU with DVFS support
system.cpu = X86O3CPU()
system.cpu.clk_domain = system.clk_domain  # Attach CPU to the clock domain

# Set pipeline depth to 5 stages
system.cpu.fetchToDecodeDelay = 1  # Fetch -> Decode
system.cpu.decodeToRenameDelay = 1  # Decode -> Rename
system.cpu.renameToIEWDelay = 1     # Rename -> Issue/Execute/Writeback
system.cpu.iewToCommitDelay = 2     # Execute -> Commit (combined stages)

# Memory configuration
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

# Instantiate caches
system.cpu.icache = L1_ICache()
system.cpu.dcache = L1_DCache()
system.l2cache = L2Cache()

# Create system buses
system.membus = SystemXBar()
system.l2bus = L2XBar()  # L1-to-L2 interconnect bus

# Connect L1 caches to CPU
system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port

# Connect L1 caches to L2 bus
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

# Connect L2 cache to L2 bus and memory bus
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# Set up CPU interrupt controller
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# System port connection
system.system_port = system.membus.cpu_side_ports

# Memory controller configuration
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Define workload and process
binary = 'tests/test-progs/hello/bin/x86/linux/hello'
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

# Instantiate simulation
root = Root(full_system=False, system=system)
m5.instantiate()
print("Starting simulation with DVFS enabled!")

# --- DVFS Simulation: Dynamically Change Frequency ---
print(f"Initial CPU clock: {system.clk_domain.clock}")

# # Simulate at 2GHz
m5.simulate(500000)

# Reduce frequency to 1GHz (Lower Power Mode)
# Can be enabled based on the battery level
system.cpu.clk_domain = system.low_power_clk_domain
print(f"Reducing CPU clock to: {system.cpu.clk_domain.clock}")
m5.simulate(500000)

# Restore frequency to 2GHz (High Performance Mode)
# Can be enabled based on the battery level/usage
system.cpu.clk_domain = system.clk_domain
print(f"Restoring CPU clock to: {system.cpu.clk_domain.clock}")
m5.simulate(500000)

# End Simulation
exit_event = m5.simulate()
print(f'Exiting at tick {m5.curTick()} due to {exit_event.getCause()}')

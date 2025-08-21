from dataclasses import dataclass
from typing import List

@dataclass
class FullMetricsConfig:
    """Configuração completa para todas as métricas do cAdvisor"""
    
    # Métricas de CPU
    cpu_metrics: List[str] = None
    
    # Métricas de Memória
    memory_metrics: List[str] = None
    
    # Métricas de Rede
    network_metrics: List[str] = None
    
    # Métricas de Disco
    disk_metrics: List[str] = None
    
    # Métricas de Processo
    process_metrics: List[str] = None
    
    # Métricas de Sistema
    system_metrics: List[str] = None
    
    # Métricas de Acelerador (GPU)
    accelerator_metrics: List[str] = None
    
    # Métricas de Huge Pages
    hugetlb_metrics: List[str] = None
    
    # Métricas de Scheduler
    scheduler_metrics: List[str] = None
    
    # Métricas TCP/UDP
    tcp_udp_metrics: List[str] = None
    
    def __post_init__(self):
        if self.cpu_metrics is None:
            self.cpu_metrics = [
                'container_cpu_usage_seconds_total',
                'container_cpu_user_seconds_total',
                'container_cpu_system_seconds_total',
                'container_cpu_cfs_periods_total',
                'container_cpu_cfs_throttled_periods_total',
                'container_cpu_cfs_throttled_seconds_total',
                'container_cpu_load_average_10s',
                'container_cpu_schedstat_run_seconds_total',
                'container_cpu_schedstat_runqueue_seconds_total',
                'container_cpu_schedstat_run_periods_total',
                'container_spec_cpu_period',
                'container_spec_cpu_quota',
                'container_spec_cpu_shares'
            ]
        
        if self.memory_metrics is None:
            self.memory_metrics = [
                'container_memory_usage_bytes',
                'container_memory_working_set_bytes',
                'container_memory_rss',
                'container_memory_cache',
                'container_memory_swap',
                'container_memory_mapped_file',
                'container_memory_failcnt',
                'container_memory_failures_total',
                'container_memory_max_usage_bytes',
                'container_spec_memory_limit_bytes',
                'container_spec_memory_swap_limit_bytes',
                'container_spec_memory_reservation_limit_bytes',
                'container_memory_kernel_usage_bytes',
                'container_memory_slab_bytes',
                'container_memory_numa_pages',
                'container_memory_numa_pages_migrated',
                'container_memory_numa_hit',
                'container_memory_numa_miss',
                'container_memory_numa_foreign'
            ]
        
        if self.network_metrics is None:
            self.network_metrics = [
                'container_network_receive_bytes_total',
                'container_network_receive_packets_total',
                'container_network_receive_packets_dropped_total',
                'container_network_receive_errors_total',
                'container_network_transmit_bytes_total',
                'container_network_transmit_packets_total',
                'container_network_transmit_packets_dropped_total',
                'container_network_transmit_errors_total',
                'container_network_tcp_usage_total',
                'container_network_tcp6_usage_total',
                'container_network_udp_usage_total',
                'container_network_udp6_usage_total',
                'container_network_tcp_usage_total',
                'container_network_advance_tcp_stats_rto_algorithm',
                'container_network_advance_tcp_stats_rto_min',
                'container_network_advance_tcp_stats_rto_max',
                'container_network_advance_tcp_stats_max_conn',
                'container_network_advance_tcp_stats_active_opens',
                'container_network_advance_tcp_stats_passive_opens',
                'container_network_advance_tcp_stats_attempt_fails',
                'container_network_advance_tcp_stats_estab_resets',
                'container_network_advance_tcp_stats_curr_estab',
                'container_network_advance_tcp_stats_in_segs',
                'container_network_advance_tcp_stats_out_segs',
                'container_network_advance_tcp_stats_retrans_segs',
                'container_network_advance_tcp_stats_in_errs',
                'container_network_advance_tcp_stats_out_rsts'
            ]
        
        if self.disk_metrics is None:
            self.disk_metrics = [
                'container_fs_usage_bytes',
                'container_fs_limit_bytes',
                'container_fs_reads_total',
                'container_fs_read_seconds_total',
                'container_fs_reads_merged_total',
                'container_fs_read_bytes_total',
                'container_fs_writes_total',
                'container_fs_write_seconds_total',
                'container_fs_writes_merged_total',
                'container_fs_write_bytes_total',
                'container_fs_io_current',
                'container_fs_io_time_seconds_total',
                'container_fs_io_time_weighted_seconds_total',
                'container_fs_inodes_free',
                'container_fs_inodes_total',
                'container_fs_sector_reads_total',
                'container_fs_sector_writes_total'
            ]
        
        if self.process_metrics is None:
            self.process_metrics = [
                'container_processes',
                'container_threads',
                'container_threads_max',
                'container_file_descriptors',
                'container_sockets',
                'container_ulimits_soft',
                'container_spec_ulimits_soft',
                'container_ulimits_hard',
                'container_spec_ulimits_hard'
            ]
        
        if self.system_metrics is None:
            self.system_metrics = [
                'container_last_seen',
                'container_start_time_seconds',
                'container_spec_cpu_period',
                'container_spec_cpu_quota',
                'container_spec_cpu_shares',
                'container_spec_memory_limit_bytes',
                'container_spec_memory_swap_limit_bytes',
                'machine_cpu_cores',
                'machine_cpu_physical_cores',
                'machine_memory_bytes',
                'machine_cpu_frequency_khz'
            ]
        
        if self.accelerator_metrics is None:
            self.accelerator_metrics = [
                'container_accelerator_memory_total_bytes',
                'container_accelerator_memory_used_bytes',
                'container_accelerator_duty_cycle',
                'container_accelerator_temperature_celsius'
            ]
        
        if self.hugetlb_metrics is None:
            self.hugetlb_metrics = [
                'container_hugetlb_usage_bytes',
                'container_hugetlb_failcnt',
                'container_hugetlb_max_usage_bytes'
            ]
        
        if self.scheduler_metrics is None:
            self.scheduler_metrics = [
                'container_cpu_schedstat_run_seconds_total',
                'container_cpu_schedstat_runqueue_seconds_total',
                'container_cpu_schedstat_run_periods_total'
            ]
        
        if self.tcp_udp_metrics is None:
            self.tcp_udp_metrics = [
                'container_network_tcp_usage_total',
                'container_network_tcp6_usage_total',
                'container_network_udp_usage_total',
                'container_network_udp6_usage_total'
            ]
    
    def get_all_metrics(self) -> List[str]:
        """Retorna todas as métricas configuradas"""
        all_metrics = []
        all_metrics.extend(self.cpu_metrics)
        all_metrics.extend(self.memory_metrics)
        all_metrics.extend(self.network_metrics)
        all_metrics.extend(self.disk_metrics)
        all_metrics.extend(self.process_metrics)
        all_metrics.extend(self.system_metrics)
        all_metrics.extend(self.accelerator_metrics)
        all_metrics.extend(self.hugetlb_metrics)
        all_metrics.extend(self.scheduler_metrics)
        all_metrics.extend(self.tcp_udp_metrics)
        return list(set(all_metrics))  # Remove duplicatas
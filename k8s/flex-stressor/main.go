// main.go - Aplicação Go para stress
package main

import (
    "fmt"
    "os"
    "runtime"
    "strconv"
    "time"
)

func cpuStress(cores int, duration time.Duration) {
    for i := 0; i < cores; i++ {
        go func() {
            end := time.Now().Add(duration)
            for time.Now().Before(end) {
                // Operação intensiva de CPU
            }
        }()
    }
}

func memoryStress(sizeMB int, duration time.Duration) {
    data := make([][]byte, 0)
    end := time.Now().Add(duration)
    
    for time.Now().Before(end) {
        chunk := make([]byte, 1024*1024) // 1MB
        data = append(data, chunk)
        if len(data) >= sizeMB {
            break
        }
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    cpuCores, _ := strconv.Atoi(os.Getenv("CPU_CORES"))
    memoryMB, _ := strconv.Atoi(os.Getenv("MEMORY_MB"))
    durationSec, _ := strconv.Atoi(os.Getenv("DURATION_SEC"))
    
    if cpuCores == 0 { cpuCores = runtime.NumCPU() }
    if memoryMB == 0 { memoryMB = 100 }
    if durationSec == 0 { durationSec = 300 }
    
    duration := time.Duration(durationSec) * time.Second
    
    fmt.Printf("Iniciando stress: CPU=%d cores, Memory=%dMB, Duration=%v\n", 
               cpuCores, memoryMB, duration)
    
    go cpuStress(cpuCores, duration)
    go memoryStress(memoryMB, duration)
    
    time.Sleep(duration)
    fmt.Println("Stress test concluído!")
}
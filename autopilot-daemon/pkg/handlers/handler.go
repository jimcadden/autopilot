package handlers

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"

	"github.ibm.com/hybrid-cloud-infrastructure-research/autopilot-daemon/pkg/utils"
	"k8s.io/klog/v2"
)

func PCIeBWHandler(pciebw string) http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Requesting pcie test with bw: " + pciebw + "\n"))

		err, out := runPCIeBw()
		if err != nil {
			klog.Error(err.Error())
		} else {
			w.Write(*out)
		}
	}
	return http.HandlerFunc(fn)
}

func RemappedRowsHandler() http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Requesting Remapped Rows check on all GPUs\n"))
		out, err := exec.Command("python3", "./gpu-remapped/entrypoint.py").Output()
		if err != nil {
			klog.Error(err.Error())
		} else {
			klog.Info("Remapped Rows check test completed:")
			// output := string(out[:])
			// fmt.Println(output)
			output := strings.TrimSuffix(string(out[:]), "\n")

			split := strings.Split(output, "\n")
			rmr := split[len(split)-1]
			final := strings.Split(rmr, " ")

			for gpuid, v := range final {
				rm, err := strconv.ParseFloat(v, 64)
				if err != nil {
					klog.Error(err.Error())
				} else {
					klog.Info("Observation: ", os.Getenv("NODE_NAME"), " ", strconv.Itoa(gpuid), " ", rm)
					utils.Hchecks.WithLabelValues("remapped", os.Getenv("NODE_NAME"), strconv.Itoa(gpuid)).Observe(rm)
					utils.HchecksGauge.WithLabelValues("remapped", os.Getenv("NODE_NAME"), strconv.Itoa(gpuid)).Set(rm)
				}
			}
		}
		w.Write(out)

	}
	return http.HandlerFunc(fn)
}

func GPUMemHandler() http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Requesting HBM test "))
	}
	return http.HandlerFunc(fn)
}

func NetReachHandler() http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Requesting secondary nics reachability test\n"))
		// utils.Hchecks.WithLabelValues("netdevice", "worker-2", "1").Observe(1.0)
		// utils.Hchecks.WithLabelValues("netdevice", "worker-2", "0").Observe(1.0)
		out, err := exec.Command("python3", "./network/metrics-entrypoint.py").Output()
		if err != nil {
			klog.Error(err.Error())
		} else {
			klog.Info("Secondary NIC health check test completed:")
			output := strings.TrimSuffix(string(out[:]), "\n")
			fmt.Println(output)
			split := strings.Split(output, "\n")
			lastline := split[len(split)-1]
			final := strings.Split(lastline, " ")
			var nicid1, nicid2 int = 1, 2
			if reachable1, err := strconv.ParseFloat(final[1], 32); err == nil {
				utils.HchecksGauge.WithLabelValues("net-reach", os.Getenv("NODE_NAME"), strconv.Itoa(nicid1)).Set(reachable1)
			}
			if reachable2, err := strconv.ParseFloat(final[2], 32); err == nil {
				utils.HchecksGauge.WithLabelValues("net-reach", os.Getenv("NODE_NAME"), strconv.Itoa(nicid2)).Set(reachable2)
			}
		}
		w.Write(out)
	}
	return http.HandlerFunc(fn)
}

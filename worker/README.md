# Worker security boundary
The control panel manages accounts and project metadata; it does not execute uploaded code.
For real deployments, run a separate private worker on a Docker-capable host. Never expose
the Docker socket or worker API publicly. Use authenticated private networking, non-root
containers, CPU/memory/PID/disk/time limits, read-only source mounts, dropped capabilities,
no-new-privileges, seccomp/AppArmor, restricted network egress, quotas, audit logs and cleanup.
Review and penetration-test this boundary before accepting untrusted user projects.

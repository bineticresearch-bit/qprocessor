# `src.network.sensor`

## `GlobalNetworkSensor`

> Orchestrates the reconstruction loop over the network sheaf.
> 
> Adapters are registered per plane; the sensor polls them each cycle,
> absorbs what they report, and (optionally) executes selected probes
> through a probe callback. All probing is rate-limited by the adapters
> themselves.

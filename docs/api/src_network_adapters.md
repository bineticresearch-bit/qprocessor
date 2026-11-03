# `src.network.adapters`

## `ChannelAdapter`

> Base class for public channel adapters.
> 
> A plane projection: raw public channel data → Observation records.
> Subclasses implement `poll()` which yields observations for the sheaf.

## `DNSAdapter`

> NAMING plane: resolve hostnames and observe A/AAAA superposition.
> 
> A dual-stack endpoint exists in superposition |IPv4⟩ + |IPv6⟩; the
> measurement collapses it. The phase encodes resolution health and
> the address-family balance.

## `CTAdapter`

> IDENTITY plane: observe certificate issuance activity.
> 
> New certificates reveal new deployments before they are announced.
> The phase encodes issuance recency; a burst of new certs is a strong
> signal of new infrastructure.

## `AtlasAdapter`

> PROBE plane: active measurements from global vantage points.
> 
> RIPE Atlas is the preferred active substrate — thousands of probes
> worldwide, with a public API and well-defined usage policies. The
> phase encodes latency and loss.

## `BGPAdapter`

> CONTROL plane: routing state from public route collectors
> (RouteViews / RIPE RIS MRT dumps).
> 
> The phase encodes route stability; withdrawals and instability map
> to unhealthy phases.

## `GPSAdapter`

> TIMING plane: clock offsets from GNSS / NTP.
> 
> Global clock synchronization reveals ionospheric events and
> infrastructure degradation. The phase encodes clock offset magnitude.

## `ConsensusAdapter`

> CONSENSUS plane: public blockchain header propagation.
> 
> Block propagation delays are a tamper-evident global heartbeat —
> congestion and partition show up as propagation anomalies.

## `SyntheticNetwork`

> A ground-truth network with known structure and state.
> 
> This is the validation substrate: the reconstructor must recover
> this network's state from sparse observations. If the model
> converges to the synthetic truth, the reconstruction loop works.
> 
> Structure:
>     root
>     └── ASes (n_ases)
>         └── prefixes (n_prefixes each)
>             └── endpoints (n_endpoints each)

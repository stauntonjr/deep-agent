# ADR-0013: Scoped DeepAgents orchestration over existing specialist services

Status: accepted for local implementation by owner instruction "begin plan execution".
Governing work: approved 2026-10-04 A2A assistant plan; GitHub Issue creation deferred.

Adapt DeepAgents and official A2A SDK rather than build an agent/protocol framework.
Application authentication and SQLite records own viewer/session/task access.
The model can investigate/read evidence, but cannot approve/save/purchase. Remote
artifacts cannot grant permissions, select service endpoints or become executable HTML.
Use process-local chat memory and durable application task history; do not claim
checkpointed conversation recovery. Human review remains disabled until the accepted
procurement contract is available. Simulation is test-only and prohibited in production.

No procurement code or deployment changes belong to this slice. OCI deployment,
real specialist integration, credentials/invitations and remote MCP availability are
separate gates. Native implementation gets one independent stable-candidate review.

Cost: bounded application state and protocol integration require ownership, timeout,
artifact and cancellation tests. Browser-native Basic authentication is temporary demo
UX. Revisit for durable chat, additional tools, production identity, protocol compatibility
or real procurement adapter mismatch. Unrestricted coding execution is deferred.

# PRD traceability fixtures

`valid/issue-144/` is a complete process package whose sidecar passes all three
stages. The sibling directories contain replacement `prd-traceability.yaml`
files under `pages/docs/` for broken-reference, duplicate-ID, version-drift,
and stage-incomplete cases. Tests copy the valid package before applying each invalid sidecar.

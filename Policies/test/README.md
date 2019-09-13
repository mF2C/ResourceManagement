# Policies Tests

To run the tests, perform the following command on the host machine where mF2C is running:

```bash
docker build --tag=test_policies . && docker run --rm --network="host" test_policies
```

#### Output Example

```text
 [PoliciesTests]  Starting...
 [PoliciesTests]  SUCCESS: Policies API working properly
 [PoliciesTests]  SUCCESS: Policies Agent Start workflow successfully started.
 [PoliciesTests]  SUCCESS: Policies sub-modules are currently running.
 [PoliciesTests]  SUCCESS: Area Resilience sub-module succesfully started.
```
# Dependencies

Dependencies control execution order between activities. The library provides small helpers that read closer to workflow code than raw `dependsOn` arrays.

## Chain activities

```python
lookup.then(copy).then(notebook)
```

By default, `.then()` creates a dependency on `Succeeded`.

## Use shorthand chaining

```python
lookup >> copy >> notebook
```

`>>` is equivalent to `.then()` and works well for linear flows.

## Branch on non-success conditions

```python
copy.then(notify, on="Failed")
copy.then(cleanup, on="Completed")
```

Supported conditions mirror Fabric dependency conditions such as `Succeeded`, `Failed`, `Completed`, and `Skipped`.

## Fan in multiple predecessors

```python
join.after(copy_a, copy_b)
```

This is useful when a later activity should wait for several parallel branches.

## Nested scopes matter

Control-flow activities such as `IfCondition`, `ForEach`, `Switch`, and `Until` contain nested activity scopes. Validation prevents cross-scope dependencies that Fabric would not accept.

## Validation catches graph mistakes

Before serialization, the pipeline graph is validated for:

- duplicate activity names
- unknown dependency targets
- cross-scope dependencies
- dependency cycles

That lets you catch orchestration mistakes in code review or CI rather than in Fabric after deployment.

`examples/etl_with_lock_pattern.py` shows cleanup wiring with `.then(..., on="Completed")`. `examples/parameterized_elt_controller.py` shows nested `ForEach` / `Switch` scopes.

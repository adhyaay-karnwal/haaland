# Haaland

**HAAL** is a token-efficient serialization language for LLM context windows: the JSON data
model, losslessly, at a fraction of the tokens.

> Initial development. Full documentation, benchmarks, and measured statistics land with v0.1.

```python
import haaland

data = {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Grace"}]}
print(haaland.dumps(data))
# users[2]{id,name}:
#  1,Ada
#  2,Grace

assert haaland.loads(haaland.dumps(data)) == data
```

## License

MIT

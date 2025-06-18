# {{ cookiecutter.module_name }} Module

## Description

Add the description of {{ cookiecutter.module_name }} here.

## Inputs/Outputs

### Required

- `sampleinput` - Describe it
- `listinput` - Ordered list 
  - `item1` (required): Describe it
  - `item2` (optional): Describe it


### Example Input

```yaml
sampleinput: "samplevalue"
listinput: 
    - item1: "lambda"
    - item2: "glue"
```

### Architecture

The above example input would translate to this architecture:

![Architecture](docs/imgs/ArchitectureDiagram.png)

## Module Metadata Outputs

- `ExampleOutput1`: Describe it
- `ExampleOutput2`: Describe it


### Output Example

```json
{
  "ExampleOutput1": "arn:aws:...",
  "ExampleOutput2": "arn:aws:...",
}
```


This project aims to provide a tool that converts diagram flows into the following formats:
- Native YAML (graphql native)
- Light YAML
- Readable YAML
- react JSON (react native)

1. Native YAML
Native YAML outputs diagrams exactly as they are in the diagram schema format provided by GraphQL. This is also called domainDiagram and represents the format directly exchanged between front-end and back-end. This file is used to execute diagrams through CLI tools or to directly verify whether the server can properly execute diagrams via curl, etc. However, it also includes position information to ensure that the location information of each node and arrow is not corrupted during the process of loading diagrams in the frontend. This format can be converted through the export function in the sidebar.

2. Light YAML
In Native YAML, handles and nodes are separated, making it difficult to view the workflow at a glance. Additionally, it contains information that is difficult to read, such as position information stored as floats and node IDs. Therefore, to make it more readable:
  - Resolve handles and include them as information within nodes
  - Convert position information to integers
  - Replace all IDs for nodes, arrows, etc. with labels. Handle IDs referenced in arrows are converted to information using node labels, etc.
  - However, to avoid duplication, if there are identical labels, additional notations such as ~1, ~2 are appended at the end.

3. Readable YAML
While Light YAML is relatively easy to read, it's still not optimized for representing diagram structures. This is especially true in that it's difficult to view each flow at a glance. To simplify this:
  - First express how each node is connected through the workflow
  - Express how data is transmitted in what form in each flow
  - Under the workflow, describe definitions for each node and person

4. react JSON
This is a file for checking how diagrams are actually rendered in the browser. It should include values such as draggable and selectable, and should be directly recognizable and renderable by React without separately defining handles.

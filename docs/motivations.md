## Why I Started This Project

* While there are already many tools that allow building agent workflows through diagrams, they surprisingly suffer from a lack of intuitiveness. For example, since agents correspond to LLMs, context, overall memory, and sandboxing are crucial - but these aspects are difficult to grasp at once with block diagrams. Moreover, even distinguishing between loops, conditionals, and agent tasks versus context wasn't intuitive even for me as a developer. I believed this issue is what makes it difficult for developers to easily move away from text-based programming.



## 프로젝트를 시작하게 된 계기:

* 다이어그램 기반으로 에이전트 워크플로를 구성할 수 있는 도구는 이미 많지만, 막상 사용해 보면 직관성이 떨어지는 경우가 많습니다. 에이전트는 결국 LLM이기 때문에 컨텍스트, 전반적인 메모리, 샌드박싱이 모두 중요한데 블록 다이어그램만으로는 이러한 요소를 한눈에 파악하기 어렵습니다. 반복문과 조건문, 에이전트의 작업과 컨텍스트를 구분하는 일도 개발자인 제 입장에서는 직감적으로 이해되지 않았고, 이 점이 개발자가 텍스트 기반 프로그래밍에서 쉽게 벗어나지 못하는 원인이라고 느꼈습니다.

## Key Concepts

* First, to intuitively represent context, the LLM instance is depicted as a “person.” A person does not forget memories even when performing tasks. Therefore, if person A completes task 1 and then person B completes task 2, when person A goes on to perform task 3, that memory must be preserved. To actively manage such situations, each person exists as a separate block as an LLM instance, and the workflow can be organized by assigning a person to each task.

* When two people are having a conversation, there may be a situation where one person periodically forgets the conversation, but the other person must remember the entire conversation. To manage this, memories are placed in a three-dimensional underground space. In other words, all of the LLM’s conversation history is stored, but if a particular person needs to forget certain parts, those conversations are severed only for that person so they cannot access them.

* This diagram system is the same as a standard diagram flow system, but it includes several mechanisms for managing loops and conditions:

    * If an arrow is connected to the “first_only” handle of a person-job block, that block will initially ignore any data coming in through its default handle. Only when it runs again will it accept data from the default handle.

    * The “max iteration” of a person-job block indicates the maximum number of times that block can execute. After reaching that number of executions, it will ignore further requests.

    * A condition block has two options: “detect max iteration” and “expression.” In the case of “detect max iteration,” it triggers when, within a cycle, all person-job blocks have reached their max iterations.

* The canvas space serves as a kind of sandbox unit, effectively an organizational unit. Here, the endpoint of a diagram becomes the endpoint of an agent system. When building an A2A (agent-to-agent) system, you can simply connect two diagrams to establish A2A. In addition, memory units are explicitly designated per diagram.

    * Since each diagram is regarded as a standard for sandbox, diagram-to-diagram network can be run in parallel. 

* Rather than merely creating diagrams, the inputs and outputs of each diagram can be exposed via API, enabling agent-based tools like Claude Code to leverage the diagrams. We aim to explore visual collaboration in which Claude Code can generate diagrams on its own or a human can modify a diagram created by Claude Code.

## Conversation system

* A conversation is always stored globally to keep track of what kind of dialogues are happening between people, and by default, every person defined in the diagram can listen to all of these conversations. 

* However, how much of the conversation each person can actually remember depends on the memory policy of the person job assigned to them. 
  * For example, if the policy is no_forget, the person remembers the entire conversation history, 
  
  * but if it’s on_every_turn, the person forgets all previous conversations each time a new request comes in. The format in which the existing conversation is included in the prompt depends on the content type delivered by the arrow—if it’s a conversation state, it gets inserted in a specific format, and if it’s raw text, it’s just inserted as plain text. 
  
* This inserted text is automatically placed at the beginning of the person job prompt, so you don’t need to set it up separately.

# 注意

本方案仅为草案，若对具体实现细节有疑问，请在评论区指出。该草案讨论事件截止到下周一（2025.10.13），届时重构方案将会定型，本discussion关闭，在Github Wiki上传新的确定版的重构方案文档。

## 现状和背景

ZSim开发进程推进至今，`Buff`模块已经成为了最大的瓶颈，也是目前开源社区参与开发的最大障碍。
所以，我们决定对Buff模块进行重构，本次重构规模极大，涉及到的功能较多，所有和Buff有关的业务逻辑都被彻底推翻重来。

- **关于数据库：**
  - 现状
    - 目前的Buff数据库分为三个部分：`触发判断.csv`、`激活判断.csv`、`buff_effect.csv`，
    - `触发判断.csv`记录了Buff的各种属性和参数，是需要保留的表，
    - `激活判断.csv`则存放了简单触发条件，在未来，这部分内容会被全新的出发判定逻辑所取代，所以这张表格的内容完全不需要；
    - `buff_effect.csv`中记录了Buff的效果；
- **现有问题：**
  - 系统耦合程度高，buff_instance直接持有sim_instance作为上下文，导致难以进行测试
  - 运行性能差，整个触发系统存在大量的重复创建Buff实例的情况，导致性能浪费严重
  - 类型提示空缺
- **重构方向**
  - Buff功能解耦：将Buff的复杂判定逻辑解耦，Buff保留`start`、`end`、`refresh`等状态管理方法
  - 数据库重构：根据新的业务架构，设计新的Buff数据库，剔除老数据库中的冗余数据，所有Buff不再以中文名（原`buff.ft.index`）作为索引值，而引入`buff.id: int`。
  - Buff触发结构重构：底层业务逻辑改写，构建起由`event_router`担任逻辑中枢的新业务逻辑
  - 重构原有的`event_listener`，将所有监听器探针交给`event_router`，修改对应角色的监听器业务逻辑。

## 新系统的思考和架构

- 新结构：
  - `GlobalBuffController`
    - `_buff_box`——内部的Buff仓库，存储本次模拟中构造的所有Buff对象。
    - `buff_initiate_factory`——原`buff_0_manager`，负责Buff初始化

    ```python
    class GlobalBuffController:
      def __init__(self):
        self._buff_box: dict[int, Buff] = defaultdict()

      def buff_register(self, buff: Buff):
        """注册传入的Buff"""
        assert buff.id not in self._buff_box.keys(), f"企图对id为{buff.id}的Buff进行重复注册！" 
        self._buff_box[buff.id] = buff

      def buff_initiate_factory(self, sim_config: "SimConfig") -> None:
        """读取配置单（SimConfig）、筛选出所有和本次模拟有关的Buff，初始化并进行注册"""
        buff_candidate_list: list[dataframe] = self.select_buff(sim_config)       # 根据配置单从数据库筛选、读取出有关buff的原数据并返回列表
        for df in buff_candidate_list:          # 构造这些Buff，存入本地的buff_box中。
          buff_new = Buff()
          self.buff_register(buff_new)
    ```

    - `BuffManager`——虽然Buff自身可以完成最基础的`start`、`end`等操作，但是角色对象持有的有效Buff的CRUD还是需要通过`BuffManager`进行的。
      - `BuffOperator`——对角色的`active_buff_list`进行操作，新增、去除Buff。

      ```python
      class GlobalBuffController:
        class BuffManager:
          class BuffOperator:
            def add_buff(self, buff: Buff, target: str | Character | ...) -> None:
              ...

            def remove_buff(self, buff: Buff, target: str | Character | ...) -> None:
              ...
      ```

  - `event_router`——解析复杂对象，触发事件。
    - `__init__`——包含一个HandlerMap、一个Buff事件树，以及一个激活事件列表。

    ```python
    from abc import ABC, abstract_method

    class EventHandler(ABC):
      @abstract_method
      def excute():     # 具体业务逻辑
        ...
    
    class SkillEventHandler(EventHandler):
      def excute():
        ...

    class EventRouter:
      def __init__(self):
        self.event_handler_map: dict[str, EventHandler] = {
          "skill_event": SkillEventHandler,
          "buff_event": BuffEventHandler,
          ...
        }     # Handler仓库，随业务拓展，在开发时，要注意所有Handler所需要的信息都通过Context传递，Context高度解耦处理。
        self.event_trigger_tree = None       # 事件触发器树
        self.active_event_list: list[ZSimEvent] = []           # 动态事件列表
      
      def update_event_list():      # 更新事件列表的业务逻辑，可能是多个函数。
        ...
      
      def register_event() -> None:      # 在触发器树中注册事件,
        ...
    ```

    - `ZSimEvent`和`EventProfile`——模拟器事件和事件画像。这是ZSim的两个重要概念，是新架构得以成立的基石。
      - `ZSimEvent`——ZSim中的事件，这里只展示基类。

      ```python
      ZSimEventType = Literal["skill_event", "anomaly_event", "schedule_preload_event", ...]
      event_type_map = {
        SkillNode: "skill_event", 
        AnomalyBar: "anomaly_event",
        SchedulePreload: "schedule_preload_event",
        ...
      }

      class ZSimEvent:
        def __init__(self, event: SkillNode | AnomalyBar | ...):
          try:
            self.event_type: ZSimEventType = event_type_map.get(type(event))
            self.event_obj = event
          except KeyError:
            raise f"未找到{type(event).__name__}类对象对应的事件类型"
        
        """对于不同的封装对象，应该构造不同的事件，这样不同的事件就可以分别重写同名方法来获取对应属性了。"""
      ```

      - `EventProfile`——事件画像类，对ZSim事件的封装。并且提供对外接口，以获取内部所封装的复杂对象的参数。

      ```python
      class EventProfile:
        def __init__(self, event_group: list[ZSimEvent]):
          self.event_group: list[ZSimEvent | None] = []
        
        def get_skill_type(self) -> int:
          ...

        def get_trigger_buff_level(self) -> int:
          ...
      ```

  - `Buff`——原`buff_class`，定义了Buff类
    - `buff_feature`——原`buff_feature`或`buff.ft`，记录了Buff的静态信息（最大持续时间、层数、更新规则）
    - `buff_dynamic`——原`buff_dynamic`或`buff.dy`，记录了Buff的动态信息（更新时间、动态层数等）
    - `bonus_class`——记录Buff效果的基类
    - `effect: effect_base_class`——`effect_base_class`类：Buff效果对象
  - `Character`和`Calculator`中进行的对应适配改动：
    - `dynamic_attribute`——重构动态属性类
      - `attribute_calculator`——负责动态属性的计算（需要调用`buff_manager.bonus_applier`）
  - `Load`阶段的关于技能事件相关的功能整合进`event_router`中。

-----------------------------------

## **关于EventRouter和新触发器系统的运作方式**

### **“事件”与“计划事件”的区别**

> ***ZSim中，抛出并立刻处理的是“事件”，而抛出后，等待未来某个tick再处理的是“计划事件”。***
> “事件”没有中转地，在被`publish`时，会被立刻调用对应的`handler`进行处理，
> 而“计划事件”则需要构造成一个新的业务类（类似于`SchedulePreload`），并将其抛入`Schedule.event_list`中，在`Schedule`阶段再进行处理。
> 在本次Buff系统重构中，绝大部分的对象都会被封装为“事件”而非“计划事件”

### **事件触发器树`event_trigger_tree`的构造**

> `event_trigger_tree`是本次重构中提出的一个新概念，在初始化时，会有一个基本的树，包含了技能事件、异常事件的节点，然后在初始化Buff的过程中，不断根据Buff的需要，在事件树中注册不同的Buff触发器事件。

### **事件画像`EventProfile`和`event_trigger_tree`的交互**

> ZSim在每个tick（频率存疑，可能还需要进一步讨论）构造一个事件画像，并且`event_trigger_tree`的各个节点调用该对象的各种方法获取自己关心的信息。一旦满足条件，就执行自身的`publish`方法，调用对应的handler实现事件的触发。

-----------------------------------

## **关于Buff系统新架构的一些重要信息**

### **Buff系统重构的基本原则：**

#### 1. *Buff是角色的一个属性，角色/Enemy对象只持有激活的Buff/Debuff*

#### 2. *仅在初始化阶段对Buff进行统一构造，模拟过程中只进行Buff信息的更新，而不重复构造。*

#### 3. *Buff负责自身状态管理：保留`buff.start`、`buff.end`、`buff.refresh`等核心状态管理方法，移除`buff.judge`、`buff.update`、`buff.exit_judge`等外部判定逻辑*

#### 4.*`event_router`将通过监听器组以及逻辑树来承担触发Buff的全部业务*

#### 5.*Buff的CRUD操作由`BuffManager`统一管理*

> ### Buff底层逻辑的变更
>
> #### **老框架：Buff自身具有判定能力**
>
> 老框架认为：需要一个专门用于判定的`Buff0`来执行`Buff.judge()`，以判定Buff是否应该触发。
> 如果在新框架中继续沿用这一内核，那么将无法摆脱`Buff0`【我们总需要一个对象来运行`Buff.judge()`，特别是在模拟器刚启动、角色尚未拥有任何Buff时】
>
>```mermaid
>graph LR
>F[外部函数] -->|直接操作| B[Buff]
>B -->|Buff判定| J[Buff.judge] 
>B -->|Buff更新| U[Buff.update]
>U -->|Buff开始| S[Buff.start]
>U -->|Buff结束判定| E[Buff.exit_judge]
>E -->|Buff结束| E1[buff.end]
>```
>
> #### **新框架：Buff负责状态管理，不负责判定**
>
> 新框架中，Buff保留了`start()`、`end()`、`refresh()`等状态管理方法，但移除了所有判定逻辑。
> Buff的触发判定完全由外部的`event_router`负责，Buff只负责在接收到信号后执行相应的状态变更。
> 这样既保持了Buff对象的完整性，又实现了系统的解耦。
>
>```mermaid
> graph LR
> A[Buff] -->|根据自身LogicID<br>注册对应Handler|B[event_router.<br>event_trigger_tree]
> E[复杂对象] -->|封装|ZE[ZSimEvent1]
> ZE -->|封装|EP
> ZE1[ZSimEvent2] -->|封装|EP[事件画像<br>EventProfile]
> ZE2[ZSimEvent3] -->|封装|EP
> ZE3[ZSimEvent4] -->|封装|EP
> ZE4[...] -->|封装|EP
> EP -->|提供信息|B
> B -->|激活|N[节点]
> N-->|执行|P[publish<br>事件]
> P -->|调用|H[BuffHandler]
> H -->|调用|B1[buff.start<br>buff.end<br>...]
> H-->|发布|B2[Buff更新事件]
> B2-->|调用|BM[BuffManager<br>执行CRUD]
> ```

## **Buff的分类**

### 注意，在理念上，这些Buff需要被进行分类，但是在实现过程中，Buff是不分类的。这里的分类讨论只是为了明确Buff的业务逻辑框架。根据Buff的功能性，我们可以将Buff分成2类

- 增减益Buff：这类Buff总是会给予对象**数值上的改变**，比如：增幅、削弱属性，影响乘区等；
- 触发器Buff：这类Buff不包含任何的数值改变，但是它的触发本身会导致一些其他事情的发生——可能是造成一些附加伤害、可能是触发别的Buff、或者是修改角色某个特殊状态等
不光是ZSim，可以说所有游戏中的Buff都可以被概括为这两个类别。
**这一Buff分类准则作为ZSimBuff系统的底层设计，在本次重构中并未改变。只是，新系统重，不同类型的Buff需要构建不同给的Handler来处理它们的业务逻辑**

## **Buff的生命周期管理（CRUD）：**

- Buff的创建
  - Buff只在初始化时被创建，在整个模拟过程中，构造函数只被调用一次。新架构中，Buff对象只有一个，由该Buff对象来统一记录、管理不同对象身上的Buff的情况（持续时间、层数等）
  - Buff在创建时，还需要根据自身的`logic_id`中记录的子条件组合，调用`event_router`的注册器，将自己注册到对应的逻辑树节点上。
- Buff的新增/刷新：
  - Buff的新增、刷新事件业务链：
    1. `event_router`提供的事件画像触发了逻辑树上的对应节点，节点激活时，会调用`publish`方法，调用`buff_event_handler`来调用buff的`start`和`end`方法，同时发布一个`buff更新事件`.
    2. `buff.start()`或者`buff.end()`方法调用时，会更新自身的信息，
    3. `BuffManager`收到`buff更新事件`时，会执行对应角色的Buff增删操作。

- Buff的查找：
  - 通过调用`buff_manager`的对应接口来实现Buff的查找
- Buff的消退：
  - Buff的消退的流程和其新增流程类似，同样是通过`event_router`或是`GlobalBuffController`抛出事件、调用对应的Handler执行。注意，部分Buff的消退不依赖于自然时间的流逝，而是具有特殊的判定行为，这部分业务交由`event_router`的逻辑树管理，Buff自身不负责判定何时消退。

-----------------------------------

## **关于Buff效果系统的重构**

### 老框架

- 通过读取`buff_effect.csv`获取Buff对应的效果`dict[str, int | float]`，然后借助`data_analyzer.py`等模块，最终在构造乘区类`MultiplierData`时，转译成各属性、乘区加成
- 缺陷：
  - `data_analyzer.py`的业务逻辑基本就是字符串解释器，扩展性较差，而且维护、拓展非常烧脑，并且运行需要传入`Generator`来构造`list[Buff]`，耦合程度太高，难以测试。
  - `MultiplierData`框架设计于立项初期，未考虑拓展和解耦，导致处理任何计算事件时都需要把全部属性、乘区都构造一遍，且生命周期极短，用完就扔，性能浪费严重，
  - `MultiplierData`没有设计供外部调用的接口，导致外部模块（例如`Buff.logic`或是`Character`）需要知道角色的动态属性时，就不得不调用大量参数就地构建一个新的`MultiplierData`

### 新框架

- 新框架将对整个系统（涉及到：`Buff`, `Character`, `Calculator`等多个模块）进行了重构，彻底实现“Buff生效”功能的解耦。
- 核心思路如下：
  1. 将属性和乘区归还给`Character`对象，一同归入`Character`的还有计算属性和乘区的一些方法
  2. 将Buff的效果对象化，并且在`Character`内部构造专门的容器用来存放效果对象，容器私有，外部只能访问`Character`提供的接口来获取所关心属性的实时加成
  3. 在`buff_effect`池和`active_buff_list`池之间，构建自动化的同步流程，保证Buff新增时，加成池同步更新（但是需要考虑类似于席德强袭Buff这种“存在但不生效”的情况）
      - 切入点：`buff_effect`自己不知道是否应该加入效果池，所以，在`active_buff_list`更新时，`buff_effect`池子默认保持更新，而独立存在一个“去除Buff效果”或者是“使Buff存在但效果静默”的事件来执行这件事情——这属于一个Buff的额外效果，需要注册到事件树中。
  4. 在`Calculator`中，对新架构进行适配（工作量略大）

### 相关重构细节如下（仅限于`buff_effect`以及角色属性、乘区相关）

- `effect_base_class`相关（新增）
  - `effect_base_class`就是本轮重构中，为“Buff效果”设计的类，专门服务于更改属性、乘区的Buff效果而创建，至于Buff触发器，将直接通过事件树进行注册，而不走`effect_base_class`路径，也不会进入`Character`的加成池。
  - 该对象的构造依赖数据库中记录的Buff效果json：

  ```json
  [
    {
      "target_attribute": "固定攻击力",
      "value": 100,
      "element_type": [1,2,3],
      "skill_tag": ["1301_SNA_1", "1301_SNA_2"]
    },
    {
      "target_attribute": "增伤",
      "value": 0.3
    },
  ]
  ```

  - 根据以上格式的`json`数据，由`Buff`对象来负责构建`Buff.effect`对象。该对象会在Buff激活时，直接加入`BuffManager.buff_effect_pool`中，注意，一个Buff对应的effect的`json`字段可能有多个，此时我们需要构造多个`effect`对象，做到一个`effect`对象仅管理一种效果。考虑到Buff的效果被分为“属性值增减益”和“事件触发器两类”，所以，设计两个继承自`effect_base_class`的类，分别处理两种不同的业务。
  - `bonus_effect_class(effect_base_class)`对象，具有属性和方法：
    - `value`：每一层Buff增幅的数值
    - `target_attribute`：增幅的项目
    - `apply_condition_list: list`：能够使Buff生效的额外条件，除`target_attribute`和`value`字段以外的其他字段，都会被视作生效条件约束，它们都会被编入`apply_judger.apply_condition_list`中
  - `trigger_class(effect_base_class)`对象，具有属性和方法：
    - 前提条件：`json`字段中含有`trigger`参数，且对应值为True时，其他参数除`event_id`以外，全部失效（当然，最好要通过pydantic进行检测，这样可以尽早暴露JSON文件填写的问题）
















- `Character`相关
  - 在`Character`下，构建一个新的`dynamic_attribute`（暂时名）类，与原有的`Statement`并列
  - 将原本属于`MultiplierData`管理的动态属性和乘区占位符合并、转移到`dynamic_attribute`下
  - 新增`attribute_calculator`对象，迁移位于`Calculator.py`中的大量计算属性、乘区的方法，业务逻辑上：通过调用`Character`原有的`Statement`方法获取静态面板，然后调用`buff_manager.bonus_applier`方法获取当前的动态加成，最后计算出实时属性。
- `Character`相关的新组件
  - `buff_effect_selector`方法，接收核心参数`environment_profile`（事件画像），该参数由外部结构`event_router`抛出，根据该对象中记录的事件标签组合，从当前激活的Buff中筛选出适配的效果
  - `bonus_applier`方法，该方法仅接受核心参数：`target_attribute`和`applied_buff_effect_list`，通过遍历`applied_buff_effect_list`，计算`target_attribute`的加成，返回给`Character.dynamic_attribute.attribute_calculator`
  - `active_buff_list`：Character级别的动态Buff列表，通过订阅Buff状态变更事件自动维护
  - `bonus_pool`：Character级别的增益池，用于存放当前激活Buff的效果，与`active_buff_list`保持同步更新，当然，也需要保留非同步更新的业务逻辑（席德Buff激活但不生效）

## **BonusPool数据结构示意图**

以下是复合字典结构在ZSim中的应用示例：

### 多字典索引结构

| Buff名称 | 攻击力相关 | 生命值相关 | 增伤区相关 | 防御区相关 |
|:---------|:-----------|:-----------|:-----------|:-----------|
| **席德-围杀** | ✅ [+100] | ❌ | ✅ [+15%] | ❌ |
| **席德-强袭** | ✅ [+200] | ❌ | ✅ [+25%] | ❌ |
| **拂晓生花-普攻增伤** | ❌ | ❌ | ✅ [+10%] | ❌ |
| **拂晓生花-四件套常驻** | ✅ [+50] | ✅ [+300] | ❌ | ❌ |
| **机巧心种-暴击** | ✅ [+12%] | ❌ | ❌ | ❌ |
| **机巧心种-电属性增伤** | ❌ | ❌ | ✅ [+20%] | ❌ |

### 对应的字典结构

```python
# 按Buff管理的字典 - 用于快速增删
_effects_by_buff = {
    1001: [attack_effect_1001, damage_bonus_effect_1001],  # 席德-围杀
    1002: [attack_effect_1002, damage_bonus_effect_1002],  # 席德-强袭
    2001: [damage_bonus_effect_2001],                     # 拂晓生花-普攻增伤
    # ...
}

# 按属性索引的字典 - 用于快速查询
_effects_by_attribute = {
    "攻击力": [attack_effect_1001, attack_effect_1002, attack_effect_2002, crit_effect_3001],
    "生命值": [hp_effect_2002],
    "增伤": [damage_bonus_effect_1001, damage_bonus_effect_1002, damage_bonus_effect_2001, damage_bonus_effect_3002],
    "防御": [],  # 当前无防御相关Buff
}
```

### 性能对比

| 操作类型 | List方案 | 多字典方案 | 性能提升 |
|:---------|:---------|:-----------|:---------|
| **查询攻击力加成** | O(N) 遍历所有Buff | O(1) 直接访问 | **~10倍** |
| **移除特定Buff** | O(1) 追加到列表 | O(K) 从多个字典移除 | **轻微增加** |
| **整体性能** | 查询密集型负载 | 查询优化型负载 | **~9-12倍** |

> **结论**：虽然增删操作略有复杂化，但查询性能的大幅提升完全值得这种设计。


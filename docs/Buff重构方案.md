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
    - `buff_initiate_factory`——原`buff_0_manager`，负责Buff初始化
  - `event_router`——解析事件，转化为结构更简单的上下文，防止复杂对象在不同阶段流动、传递。
    - `event_label_factory`——负责事件解析，将事件标签化，返回`environment_profile`（事件画像）
    - `buff_filter`——根据事件画像，筛选出可能触发的Buff（缩小遍历范围）
    - `condition_evaluator`——负责遍历`event_router`筛选出的Buff集，通过Buff记录的`logic_id`调用对应的逻辑判定脚本，结合传入的事件标签，决定Buff是否触发
    - `buff_activator`——调用`BuffManager`实现Buff的触发
    - `buff_terminator`——负责调用`BuffManager`实现Buff的终止
  - `BuffManager`——全局Buff管理器，负责对所有Buff进行CRUD操作
    - `buff_box`——全局Buff实例的存储地，存储所有Buff对象
    - `buff_operator`——实现Buff的查找、注册等基础操作
  - `Buff`——原`buff_class`，定义了Buff类
    - `buff_feature`——原`buff_feature`或`buff.ft`，记录了Buff的静态信息（最大持续时间、层数、更新规则）
    - `buff_dynamic`——原`buff_dynamic`或`buff.dy`，记录了Buff的动态信息（更新时间、动态层数等）
    - `bonus_class`——记录Buff效果的基类
    - `effect: effect_base_class`——`effect_base_class`类：Buff效果对象
  - `Character`和`Calculator`中进行的对应适配改动：
    - `dynamic_attribute`——重构动态属性类
      - `attribute_calculator`——负责动态属性的计算（需要调用`buff_manager.bonus_applier`）

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
> A[buff_manager] -->|委托调用| B[Buff.start/end]
> C[event_router] -->|发布触发事件|S[Schedule]
> S -->|执行触发事件<br>抛出触发信号| H[buff_active_handler]
> H -->|调用BuffManager| A
> A -->|委托执行| B
> ```

## **Buff的分类**

### 注意，在理念上，这些Buff需要被进行分类，但是在实现过程中，Buff是不分类的。这里的分类讨论只是为了明确Buff的业务逻辑框架。根据Buff的功能性，我们可以将Buff分成2类

- 增减益Buff：这类Buff总是会给予对象**数值上的改变**，比如：增幅、削弱属性，影响乘区等；
- 触发器Buff：这类Buff不包含任何的数值改变，但是它的触发本身会导致一些其他事情的发生——可能是造成一些附加伤害、可能是触发别的Buff、或者是修改角色某个特殊状态等
不光是ZSim，可以说所有游戏中的Buff都可以被概括为这两个类别。
**这一Buff分类准则作为ZSimBuff系统的底层设计，在本次重构中并未改变。**

## **Buff的生命周期管理（CRUD）：**

- Buff的创建
  - Buff只在初始化时被创建，在整个模拟过程中，构造函数只被调用一次。新架构中，Buff对象只有一个，由该Buff对象来统一记录、管理不同对象身上的Buff的情况（持续时间、层数等）
  - Buff在创建时，还需要根据自身的`logic_id`中记录的子条件组合，调用`event_router`的注册器，将自己注册到对应的逻辑树节点上。
- Buff的新增/刷新：
  - Buff的新增、刷新事件业务链：
    1. `event_router`提供的事件画像触发了逻辑树上的对应节点，此时节点会抛出一个触发事件`BuffTriggerEvent`，
    2. 在Schedule阶段，该事件会被解析，并且于对应的时间执行，转化为更新信号`EventExcuteSignal`类，其中记录了Buff的ID、本次新增的受益人、新增的层数、时间等信息，
    3. 信号被传输给`EventHander`，并且被对应的`buff_update_hander`接收，
    4. `buff_update_hander`接收信号后，调用`buff_manager`的对应方法`buff_start`，执行Buff的新增，该方法只接受一个`EventExcuteSignal`类，该方法通过`buff.id`为键值，直接访问内部的Buff仓库，找到对应Buff对象，并且修改其`buff.dynamic`下的对应参数。
- Buff的查找：
  - 通过调用`buff_manager`的对应接口来实现Buff的查找
- Buff的消退：
  - Buff的消退的流程和其新增流程类似，同样是通过`event_router`抛出事件、Schedule抛出信号、被对应的Handler接收、最后调用`buff.end()`执行。注意，部分Buff的消退不依赖于自然时间的流逝，而是具有特殊的判定行为，这部分业务交由`event_router`的逻辑树管理，Buff自身不负责判定何时消退。

    ```mermaid
        flowchart LR
    A[事件画像] --> B[逻辑树节点]
    B --> C[抛出BuffTriggerEvent]
    C --> D[Schedule阶段]
    D --> E[解析事件]
    E --> F[生成EventExcuteSignal]
    F --> G[EventHander]
    G --> H[buff_update_hander]
    H --> I[buff_manager.buff_start]
    I --> J[访问Buff仓库]
    J --> K[委托Buff执行状态更新]
    
    subgraph 事件触发阶段
        A --> B --> C
    end
    
    subgraph 调度执行阶段
        D --> E --> F
    end
    
    subgraph 信号处理阶段
        G --> H --> I
    end
    
    subgraph Buff更新阶段
        J --> K
    end
    ```

    ```python
    from dataclasses import dataclass
    from typing import Literal, Optional, Dict, List

    @dataclass
    class BuffUpdateSignal:
        """Buff更新信号，用于传递Buff的动态信息"""
        buff_id: int
        beneficiary: int            # 受益人CID
        start_tick: int
        end_tick: int
        count: int | float

    @dataclass
    class BuffAddSignal(EventExcuteSignal):
        """Buff添加信号，继承自事件执行信号基类"""
        buff_id: int
        buff_operation_type: Literal["start", "end"]
        buff_update_info: List[BuffUpdateSignal]

    class BuffManager:
        """全局Buff管理器，负责对所有Buff进行CRUD操作"""
        def __init__(self):
            self._buff_inventory: Dict[int, Buff] = {}       # {buff.id: buff对象}

        def start_buff(self, signal: BuffUpdateSignal) -> None:
            """启动Buff，委托给Buff对象执行具体逻辑"""
            buff = self._buff_inventory.get(signal.buff_id, None)
            assert buff is not None, f"未找到ID为{signal.buff_id}的Buff"

            # 委托给Buff对象执行启动逻辑
            buff.start(signal)

        def end_buff(self, signal: BuffUpdateSignal) -> None:
            """结束Buff，委托给Buff对象执行具体逻辑"""
            buff = self._buff_inventory.get(signal.buff_id, None)
            assert buff is not None, f"未找到ID为{signal.buff_id}的Buff"

            # 委托给Buff对象执行结束逻辑
            buff.end(signal)

    ```

    ```python
    class Buff:
        """Buff类，定义了Buff的基础行为和数据结构"""
        def __init__(self, buff_id: int):
            self.id = buff_id
            self.feature = BuffFeature()    # 静态特征（最大持续时间、层数等）
            self.dynamic = BuffDynamic()    # 动态状态（当前持续时间、层数等）
            self.effect_list: List[effect_base_class] = []  # Buff效果列表

        def start(self, signal: BuffUpdateSignal) -> None:
            """启动Buff，更新动态信息并激活效果"""
            # 更新动态状态
            self.dynamic.start_tick = signal.start_tick
            self.dynamic.end_tick = signal.end_tick
            self.dynamic.count = signal.count
            self.dynamic.is_active = True

            # 执行启动时的内部逻辑
            self._on_start()

        def end(self, signal: BuffUpdateSignal) -> None:
            """结束Buff，清理动态信息"""
            # 重置动态状态
            self.dynamic.is_active = False
            self.dynamic.start_tick = 0
            self.dynamic.end_tick = 0
            self.dynamic.count = 0

            # 执行结束时的内部逻辑
            self._on_end()

        def refresh(self, signal: BuffUpdateSignal) -> None:
            """刷新Buff，根据特性决定刷新策略"""
            if self.feature.refresh_rule == "extend":
                # 延长时间：新结束时间 = 当前tick + 持续时间
                self.dynamic.end_tick = max(
                    self.dynamic.end_tick,
                    signal.start_tick + self.feature.duration
                )
            elif self.feature.refresh_rule == "reset":
                # 重置时间
                self.dynamic.start_tick = signal.start_tick
                self.dynamic.end_tick = signal.end_tick

            # 更新层数（如果是叠加类Buff）
            if self.feature.can_stack:
                self.dynamic.count = min(
                    signal.count,
                    self.feature.max_stack
                )

            # 执行刷新时的内部逻辑
            self._on_refresh()

        def is_active(self, current_tick: int) -> bool:
            """检查Buff是否处于激活状态"""
            return (self.dynamic.is_active and
                   self.dynamic.start_tick <= current_tick <= self.dynamic.end_tick)

        # 私有方法，保证内部状态一致性
        def _on_start(self) -> None:
            """Buff启动时的内部逻辑"""
            # 准备效果对象
            for effect in self.effect_list:
                effect.on_buff_start(self)

        def _on_end(self) -> None:
            """Buff结束时的内部逻辑"""
            # 清理效果对象
            for effect in self.effect_list:
                effect.on_buff_end(self)

        def _on_refresh(self) -> None:
            """Buff刷新时的内部逻辑"""
            # 刷新相关效果
            for effect in self.effect_list:
                effect.on_buff_refresh(self)
    ```


# **事件画像与事件标签**
> ### 条件 即 事件（底层逻辑！！）
> #### 事件画像`environment_profile`是本次重构中提出的一个新概念。
> 由于**"Buff的触发依赖事件**的这一底层逻辑并未改变，所以ZSim的新Buff系统的运行依旧需要明确的事件信号。
> 在以往，这一信号往往是通过直接传递事件本身（`SkillNode | AnomalyBar | ……`）以及其他附带的简单`str`格式的上下文来实现的。
> 而新的Buff系统为了实现解耦，必须要避免直接传递事件对象本身，
> 所以我们安排`event_router`对事件进行解析，拆解成事件标签`event_label`，并且封装进事件画像`environment_profile`中。
>> 注意：模拟器中某个tick的事件画像可能是极为复杂的，如果仅从"抽象描绘事件和环境"的角度出发，我们难以得到最简练的事件画像。
>> 由于事件画像目前仅服务于Buff系统（在肉眼可见的未来，它的服务对象或有拓展，但是方式不会有巨大的改变），
>> 我们完全可以根据需求侧的情况，来定制事件标签的种类。
>> 即，我们需要一个"标签仓库"，来存放目前已经开发的Buff所有可能用到的标签，并且对他们进行归纳、分类。
>> 而`event_router`在构建事件画像时，仅根据这个"标签仓库"中已有的标签类别进行构建。
>> 这样，我们就实现了标签类的最简化处理，还能满足所有的Buff触发的需求。
> 以上，就是我们在重构会议中提到的——**条件 即 事件**。
> ```mermaid
> graph LR
>     A[原始事件] --> B[event_router]
>     B --> C[事件解析]
>     D[标签仓库] --> C
>     C --> E[生成事件标签]
>     E --> F[封装事件画像]
>     F --> G[Buff系统判定]
>     G --> H[Buff触发]
> ```


# **关于Buff效果系统的重构**
## 老框架
- 通过读取`buff_effect.csv`获取Buff对应的效果`dict[str, int | float]`，然后借助`data_analyzer.py`等模块，最终在构造乘区类`MultiplierData`时，转译成各属性、乘区加成
- 缺陷：
  - `data_analyzer.py`的业务逻辑基本就是字符串解释器，扩展性较差，而且维护、拓展非常烧脑，并且运行需要传入`Generator`来构造`list[Buff]`，耦合程度太高，难以测试。
  - `MultiplierData`框架设计于立项初期，完全做拆分，算任何属性都需要把全部属性、乘区都构造一遍，且生命周期极短，用完就扔，性能浪费严重，
  - `MultiplierData`没有设计供外部调用的接口，导致外部模块（例如`Buff.logic`或是`Character`）需要知道角色的动态属性时，就不得不调用大量参数就地构建一个新的`MultiplierData`

---------------------------
## 新框架
- 新框架将对整个系统（涉及到：`Buff`, `Character`, `Calculator`等多个模块）进行了重构，彻底实现“Buff生效”功能的解耦。
## 相关重构细节如下（仅限于`buff_effect`以及角色属性、乘区相关）：
- `Character`相关
  - 在`Character`下，构建一个新的`dynamic_attribute`（暂时名）类，与原有的`Statement`并列
  - 将原本属于`MultiplierData`管理的动态属性和乘区占位符合并、转移到`dynamic_attribute`下
  - 新增`attribute_calculator`对象，迁移位于`Calculator.py`中的大量计算属性、乘区的方法，业务逻辑上：通过调用`Character`原有的`Statement`方法获取静态面板，然后调用`buff_manager.bonus_applier`方法获取当前的动态加成，最后计算出实时属性。
- `Character`相关的新组件
  - `buff_effect_selector`方法，接收核心参数`environment_profile`（事件画像），该参数由外部结构`event_router`抛出，根据该对象中记录的事件标签组合，从当前激活的Buff中筛选出适配的效果
  - `bonus_applier`方法，该方法仅接受核心参数：`target_attribute`和`applied_buff_effect_list`，通过遍历`applied_buff_effect_list`，计算`target_attribute`的加成，返回给`Character.dynamic_attribute.attribute_calculator`
  - `active_buff_list`：Character级别的动态Buff列表，通过订阅Buff状态变更事件自动维护
  - `bonus_pool`：Character级别的增益池，用于存放当前激活Buff的效果，与`active_buff_list`保持同步更新，当然，也需要保留非同步更新的业务逻辑（席德Buff激活但不生效）
- `effect_base_class`相关（新增）
  - 构建一个用于传递“Buff效果信息”的基类`effect_base_class`（暂时名），这些`effect_base_class`记录了增益种类、数值，或者是触发器的触发事件。
  - 通过读取数据库中以`json`格式存储的数据

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
		  {
			  "trigger": true,
			  "event_id": 10030
		  }
	  ]
```
  - 根据以上格式的`json`数据，由`Buff`对象来负责构建`Buff.effect`对象。该对象会在Buff激活时，直接加入`BuffManager.buff_effect_pool`中，注意，一个Buff对应的effect的`json`字段可能有多个，此时我们需要构造多个`effect`对象，做到一个`effect`对象仅管理一种效果。考虑到Buff的效果被分为“属性值增减益”和“事件触发器两类”，所以，设计两个继承自`effect_base_class`的类，分别处理两种不同的业务。
  - `bonus_effect_class(effect_base_class)`对象，具有属性和方法：
    - `value`：每一层Buff增幅的数值
    - `target_attribute`：增幅的项目
    - `apply_condition_list: list`：能够使Buff生效的额外条件，除`target_attribute`和`value`字段以外的其他字段，都会被视作生效条件约束，它们都会被编入`apply_judger.apply_condition_list`中
  - `trigger_class(effect_base_class)`对象，具有属性和方法：
    - 前提条件：`json`字段中含有`trigger`参数，且对应值为True时，其他参数除`event_id`以外，全部失效（当然，最好要通过pydantic进行检测，这样可以尽早暴露JSON文件填写的问题）

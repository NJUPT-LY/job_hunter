from typing import List
from app.models.schemas import ActionItem


class ActionPlanGenerator:
    
    @classmethod
    def generate(cls, job_title: str, user_profile: dict) -> List[ActionItem]:
        templates = cls._get_plan_templates()
        
        category = cls._detect_category(job_title)
        base_plan = templates.get(category, templates.get("通用"))
        
        plan = []
        for phase_data in base_plan:
            item = ActionItem(
                phase=phase_data["phase"],
                title=phase_data["title"].format(job=job_title),
                description=phase_data["description"].format(job=job_title),
                tasks=phase_data["tasks"],
                resources=phase_data.get("resources", []),
                completed=False
            )
            plan.append(item)
        
        return plan
    
    @classmethod
    def get_templates(cls) -> dict:
        return {
            "技术": cls._get_plan_templates().get("技术"),
            "产品": cls._get_plan_templates().get("产品"),
            "数据分析": cls._get_plan_templates().get("数据分析"),
            "通用": cls._get_plan_templates().get("通用")
        }
    
    @classmethod
    def _detect_category(cls, job_title: str) -> str:
        if any(kw in job_title for kw in ["前端", "后端", "开发", "工程师", "Python", "Java", "C++"]):
            return "技术"
        elif "产品" in job_title:
            return "产品"
        elif "数据" in job_title:
            return "数据分析"
        elif "设计" in job_title:
            return "设计"
        elif "运营" in job_title or "市场" in job_title:
            return "运营"
        return "通用"
    
    @classmethod
    def _get_plan_templates(cls) -> dict:
        return {
            "技术": [
                {
                    "phase": "阶段1：基础知识巩固",
                    "title": "夯实{job}基础知识",
                    "description": "系统学习目标岗位所需的基础知识，建立扎实的理论基础",
                    "tasks": [
                        "复习编程语言核心语法和特性",
                        "学习数据结构和算法基础",
                        "掌握计算机网络和操作系统基础",
                        "完成1-2门相关在线课程"
                    ],
                    "resources": [
                        "《算法导论》或LeetCode初级题目",
                        "慕课网/极客时间相关课程",
                        "官方文档和教程"
                    ]
                },
                {
                    "phase": "阶段2：技能提升",
                    "title": "学习{job}核心框架和工具",
                    "description": "深入学习目标岗位常用的框架、工具和最佳实践",
                    "tasks": [
                        "学习主流开发框架并完成官方教程",
                        "了解常用中间件和数据库",
                        "学习版本控制工具Git",
                        "了解基本的DevOps流程"
                    ],
                    "resources": [
                        "框架官方文档",
                        "GitHub开源项目学习",
                        "技术博客和社区"
                    ]
                },
                {
                    "phase": "阶段3：项目实践",
                    "title": "完成2-3个{job}相关项目",
                    "description": "通过实际项目巩固所学知识，积累可展示的作品",
                    "tasks": [
                        "完成1个个人项目（如个人网站/博客）",
                        "参与1个开源项目或团队项目",
                        "完成1个与目标岗位相关的项目",
                        "将代码上传至GitHub并编写README"
                    ],
                    "resources": [
                        "GitHub作为代码托管平台",
                        "产品创意可从日常需求中发现",
                        "参考优秀开源项目的结构"
                    ]
                },
                {
                    "phase": "阶段4：作品集准备",
                    "title": "整理{job}作品集和简历",
                    "description": "将项目经历整理成作品集，优化简历突出与目标岗位匹配的能力",
                    "tasks": [
                        "整理GitHub项目，完善README文档",
                        "编写项目总结和技术博客",
                        "使用STAR法则撰写项目经历",
                        "准备技术面试常见问题"
                    ],
                    "resources": [
                        "技术博客平台（掘金、CSDN等）",
                        "简历模板和范例",
                        "面试题库"
                    ]
                },
                {
                    "phase": "阶段5：面试冲刺",
                    "title": "{job}面试准备与模拟",
                    "description": "集中进行面试模拟和复习，查漏补缺，提升面试表现",
                    "tasks": [
                        "刷LeetCode/面试真题（每天5-10题）",
                        "复习八股文和基础知识",
                        "进行模拟面试（至少3次）",
                        "准备自我介绍和项目介绍"
                    ],
                    "resources": [
                        "LeetCode/牛客网题库",
                        "面经汇总（牛客、知乎）",
                        "模拟面试工具"
                    ]
                }
            ],
            "产品": [
                {
                    "phase": "阶段1：产品思维建立",
                    "title": "建立产品思维和基础能力",
                    "description": "学习产品经理的核心思维方式和基础工作方法",
                    "tasks": [
                        "阅读产品经典书籍（《启示录》《结网》）",
                        "学习用户研究方法和需求分析",
                        "了解产品开发全流程",
                        "学习原型设计工具使用"
                    ],
                    "resources": [
                        "《启示录》《结网》《人人都是产品经理》",
                        "Axure/Figma教程",
                        "产品经理社区（PMCAFF等）"
                    ]
                },
                {
                    "phase": "阶段2：工具技能掌握",
                    "title": "掌握{job}必备工具",
                    "description": "熟练使用产品工作所需的各类工具",
                    "tasks": [
                        "熟练使用Axure或Figma绘制原型",
                        "学习使用XMind等思维导图工具",
                        "学习基础的数据分析方法",
                        "学习撰写PRD文档"
                    ],
                    "resources": [
                        "工具官方教程",
                        "产品原型案例",
                        "数据分析入门课程"
                    ]
                },
                {
                    "phase": "阶段3：项目实践",
                    "title": "完成产品项目实践",
                    "description": "通过实际项目积累产品经验",
                    "tasks": [
                        "选择一款产品进行深度分析和改进方案设计",
                        "完成一份完整的产品需求文档",
                        "参与校园项目或创业比赛",
                        "争取产品相关实习机会"
                    ],
                    "resources": [
                        "优秀产品分析报告",
                        "PRD模板",
                        "实习招聘平台"
                    ]
                },
                {
                    "phase": "阶段4：求职准备",
                    "title": "{job}求职材料准备",
                    "description": "准备求职所需的材料和作品集",
                    "tasks": [
                        "整理产品分析报告作为作品集",
                        "用STAR法则撰写项目/实习经历",
                        "准备产品案例分析练习",
                        "进行模拟面试"
                    ],
                    "resources": [
                        "产品作品集模板",
                        "产品面经",
                        "模拟面试工具"
                    ]
                }
            ],
            "数据分析": [
                {
                    "phase": "阶段1：基础能力建立",
                    "title": "建立{job}基础知识体系",
                    "description": "系统学习数据分析所需的统计学和编程基础",
                    "tasks": [
                        "学习概率论与数理统计基础",
                        "掌握SQL基本语法和常用操作",
                        "学习Python基础及Pandas/NumPy",
                        "学习Excel高级功能"
                    ],
                    "resources": [
                        "《统计学》教材",
                        "SQLZoo/LeetCode SQL题目",
                        "Python数据分析相关课程"
                    ]
                },
                {
                    "phase": "阶段2：工具与方法",
                    "title": "掌握{job}分析工具和方法",
                    "description": "学习数据分析常用工具和分析方法论",
                    "tasks": [
                        "学习数据可视化工具（Tableau/PowerBI）",
                        "学习A/B测试方法",
                        "学习常用的数据分析模型",
                        "练习使用真实数据集进行分析"
                    ],
                    "resources": [
                        "Kaggle数据集",
                        "Tableau官方教程",
                        "数据分析案例"
                    ]
                },
                {
                    "phase": "阶段3：项目实战",
                    "title": "完成{job}分析项目",
                    "description": "通过实际分析项目展示能力",
                    "tasks": [
                        "在Kaggle完成1-2个数据分析项目",
                        "撰写分析报告并发布",
                        "建立个人数据分析作品集",
                        "参与数据分析相关比赛"
                    ],
                    "resources": [
                        "Kaggle/Tianchi平台",
                        "GitHub Pages展示作品",
                        "技术博客"
                    ]
                },
                {
                    "phase": "阶段4：求职冲刺",
                    "title": "{job}求职准备",
                    "description": "集中准备面试和求职材料",
                    "tasks": [
                        "整理数据分析作品集",
                        "准备SQL和技术面试题目",
                        "练习业务分析案例题",
                        "进行模拟面试"
                    ],
                    "resources": [
                        "SQL面试题汇总",
                        "数据分析面经",
                        "模拟面试工具"
                    ]
                }
            ],
            "通用": [
                {
                    "phase": "阶段1：自我认知与目标明确",
                    "title": "明确{job}方向和目标",
                    "description": "了解自己的兴趣和优势，确定职业方向",
                    "tasks": [
                        "进行职业兴趣测试和性格测试",
                        "研究目标岗位的真实工作内容",
                        "了解行业趋势和岗位需求",
                        "确定2-3个目标岗位方向"
                    ],
                    "resources": [
                        "霍兰德职业兴趣测试",
                        "招聘网站岗位描述",
                        "行业报告"
                    ]
                },
                {
                    "phase": "阶段2：能力差距分析",
                    "title": "分析{job}能力差距并制定计划",
                    "description": "对比目标岗位要求，找出差距并制定学习计划",
                    "tasks": [
                        "列出目标岗位的核心技能要求",
                        "评估自己的现有能力水平",
                        "制定优先级学习计划",
                        "设定阶段性目标"
                    ],
                    "resources": [
                        "岗位JD分析工具",
                        "技能评估问卷",
                        "学习规划模板"
                    ]
                },
                {
                    "phase": "阶段3：能力提升",
                    "title": "系统性提升{job}所需能力",
                    "description": "按照计划系统学习，补齐能力短板",
                    "tasks": [
                        "完成核心课程学习",
                        "参与相关项目实践",
                        "考取相关证书（如有需要）",
                        "寻找实习机会"
                    ],
                    "resources": [
                        "在线学习平台",
                        "校园项目资源",
                        "实习信息渠道"
                    ]
                },
                {
                    "phase": "阶段4：求职准备",
                    "title": "准备{job}求职材料",
                    "description": "完成简历、作品集等求职材料",
                    "tasks": [
                        "撰写并优化简历",
                        "整理项目经历和作品集",
                        "准备面试常见问题",
                        "进行模拟面试练习"
                    ],
                    "resources": [
                        "简历模板",
                        "面试题库",
                        "模拟面试工具"
                    ]
                }
            ]
        }

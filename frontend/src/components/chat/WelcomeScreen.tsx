import { Bot, TrendingUp, Globe, Sparkles, Users, UserCircle2, NotebookPen } from "lucide-react";

interface Example {
  title: string;
  desc: string;
  prompt: string;
}

interface Category {
  label: string;
  icon: React.ReactNode;
  color: string;
  examples: Example[];
}

const CATEGORIES: Category[] = [
  {
    label: "多市场回测",
    icon: <TrendingUp className="h-4 w-4" />,
    color: "text-red-400 border-red-500/30 hover:border-red-500/60 hover:bg-red-500/5",
    examples: [
      {
        title: "跨市场组合",
        desc: "A 股 + 加密货币 + 美股，使用风险平价优化器",
        prompt: "回测 000001.SZ、BTC-USDT 和 AAPL 的风险平价组合，时间为 2024 全年，并和等权基准比较",
      },
      {
        title: "BTC 5 分钟 MACD 策略",
        desc: "基于 OKX 实时数据的分钟级加密货币回测",
        prompt: "回测 BTC-USDT 5 分钟 MACD 策略，fast=12 slow=26 signal=9，最近 30 天",
      },
      {
        title: "美股科技股最大分散化",
        desc: "通过 yfinance 对 FAANG+ 组合做优化",
        prompt: "回测 AAPL、MSFT、GOOGL、AMZN、NVDA，使用 max_diversification 组合优化器，时间为 2024 全年",
      },
    ],
  },
  {
    label: "研究与分析",
    icon: <Sparkles className="h-4 w-4" />,
    color: "text-amber-400 border-amber-500/30 hover:border-amber-500/60 hover:bg-amber-500/5",
    examples: [
      {
        title: "多因子 Alpha 模型",
        desc: "在 300 只股票上进行 IC 加权因子合成",
        prompt: "使用动量、反转、波动率和换手率，在沪深 300 成分股上构建多因子 alpha 模型，用 IC 加权合成，回测 2023-2024",
      },
      {
        title: "期权 Greeks 分析",
        desc: "Black-Scholes 定价与 Delta/Gamma/Theta/Vega",
        prompt: "使用 Black-Scholes 计算期权 Greeks：spot=100，strike=105，risk-free rate=3%，vol=25%，expiry=90 days，并分析 Delta/Gamma/Theta/Vega",
      },
    ],
  },
  {
    label: "智能体团队",
    icon: <Users className="h-4 w-4" />,
    color: "text-violet-400 border-violet-500/30 hover:border-violet-500/60 hover:bg-violet-500/5",
    examples: [
      {
        title: "投委会评审",
        desc: "多智能体辩论：多空观点、风险评审、PM 决策",
        prompt: "[Swarm Team Mode] 使用 investment_committee 预设，基于当前市场环境评估 NVDA 应该做多还是做空",
      },
      {
        title: "量化策略台",
        desc: "筛选、因子研究、回测、风险审计流水线",
        prompt: "[Swarm Team Mode] 使用 quant_strategy_desk 预设，在沪深 300 成分股中寻找并回测最佳动量策略",
      },
    ],
  },
  {
    label: "文档与网页研究",
    icon: <Globe className="h-4 w-4" />,
    color: "text-blue-400 border-blue-500/30 hover:border-blue-500/60 hover:bg-blue-500/5",
    examples: [
      {
        title: "分析财报 PDF",
        desc: "上传 PDF 后提问财务数据、风险与展望",
        prompt: "总结已上传财报中的关键财务指标、风险和业务展望",
      },
      {
        title: "网页研究：宏观展望",
        desc: "读取实时网页来源进行宏观分析",
        prompt: "读取最新美联储会议纪要，并总结对股票和加密货币市场的关键影响",
      },
    ],
  },
  {
    label: "交易日志",
    icon: <NotebookPen className="h-4 w-4" />,
    color: "text-orange-400 border-orange-500/30 hover:border-orange-500/60 hover:bg-orange-500/5",
    examples: [
      {
        title: "分析券商导出记录",
        desc: "解析同花顺/东财/富途/通用 CSV，统计持仓天数、胜率、盈亏比和时段分布",
        prompt: "分析我刚上传的交易日志，生成完整画像：持仓统计、胜率、主要交易标的和小时分布",
      },
      {
        title: "诊断交易行为偏差",
        desc: "处置效应、过度交易、追涨、锚定，给出严重程度和数值证据",
        prompt: "对我的交易日志运行 4 项行为诊断（处置效应、过度交易、追涨、锚定），告诉我哪个偏差最伤害 PnL",
      },
    ],
  },
  {
    label: "Shadow Account",
    icon: <UserCircle2 className="h-4 w-4" />,
    color: "text-emerald-400 border-emerald-500/30 hover:border-emerald-500/60 hover:bg-emerald-500/5",
    examples: [
      {
        title: "从日志训练我的 Shadow",
        desc: "从券商 CSV 中提取你的策略规则并保存 Shadow 档案",
        prompt: "用我刚上传的交易日志训练 shadow account，展示提取出的规则，并确认这些规则是否像我的真实行为",
      },
      {
        title: "我错过了多少收益？",
        desc: "回测你的 Shadow 策略，并归因它与真实 PnL 的差异",
        prompt: "对最近 90 天美股市场运行 shadow 回测，拆解我的 PnL 和 shadow 的差异来源（规则违背、过早退出、错过信号）",
      },
      {
        title: "生成 Shadow 报告",
        desc: "8 节 HTML/PDF 报告：权益曲线、分市场 Sharpe、归因瀑布图",
        prompt: "渲染 shadow 报告并给我 URL，先展示我和 shadow 的收益差异",
      },
    ],
  },
];

const CAPABILITY_CHIPS = [
  "70 个金融技能",
  "29 个团队预设",
  "32 个智能体工具",
  "3 类市场：A 股 · 加密货币 · 港/美股",
  "分钟到日线周期",
  "4 种组合优化器",
  "15+ 风险指标",
  "期权与衍生品",
  "PDF 与网页研究",
  "因子分析与机器学习",
  "交易日志分析",
  "Shadow Account 回测",
  "持久记忆",
  "会话搜索",
];

interface Props {
  onExample: (s: string) => void;
}

export function WelcomeScreen({ onExample }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 text-center">
      <div className="space-y-3">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-gradient-to-br from-primary/80 to-info/80 flex items-center justify-center shadow-lg">
          <Bot className="h-8 w-8 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Vibe-Trading</h2>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto leading-relaxed">
            你的专业金融智能体团队
          </p>
          <p className="text-sm text-muted-foreground mt-2 max-w-md leading-relaxed mx-auto">
            描述一个交易策略即可开始。
          </p>
        </div>
      </div>

      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        {CAPABILITY_CHIPS.map((chip) => (
          <span
            key={chip}
            className="px-2.5 py-1 text-xs rounded-full border border-border/60 text-muted-foreground bg-muted/30"
          >
            {chip}
          </span>
        ))}
      </div>

      <div className="w-full max-w-2xl text-left space-y-4">
        <p className="text-xs text-muted-foreground px-1">试试这些示例：</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {CATEGORIES.map((cat) => (
            <div key={cat.label} className="space-y-2">
              <div className={`flex items-center gap-1.5 text-xs font-medium px-1 ${cat.color.split(" ").filter(c => c.startsWith("text-")).join(" ")}`}>
                {cat.icon}
                <span>{cat.label}</span>
              </div>
              <div className="space-y-1.5">
                {cat.examples.map((ex) => (
                  <button
                    key={ex.title}
                    onClick={() => onExample(ex.prompt)}
                    className={`block w-full text-left px-3 py-2.5 rounded-xl border transition-colors ${cat.color}`}
                  >
                    <span className="text-sm font-medium text-foreground leading-snug">
                      {ex.title}
                    </span>
                    <span className="block text-xs text-muted-foreground mt-0.5 leading-snug">
                      {ex.desc}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

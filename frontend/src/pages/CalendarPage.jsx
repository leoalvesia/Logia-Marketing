import { useState, useMemo } from "react";
import {
    DndContext,
    DragOverlay,
    PointerSensor,
    useSensor,
    useSensors,
    useDroppable,
    useDraggable,
} from "@dnd-kit/core";
import { Plus, ChevronLeft, ChevronRight, CalendarDays, LayoutList } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { MOCK_CALENDAR_EVENTS } from "@/data/mockLibrary";

// ── Channel config ────────────────────────────────────────────────────────────

const CHANNEL_COLORS = {
    instagram: { bg: "bg-pink-950/70", border: "border-pink-700/60", text: "text-pink-300", dot: "#EC4899" },
    linkedin: { bg: "bg-blue-950/70", border: "border-blue-700/60", text: "text-blue-300", dot: "#0A66C2" },
    twitter: { bg: "bg-zinc-800/80", border: "border-zinc-600/60", text: "text-zinc-300", dot: "#E7E9EA" },
    youtube: { bg: "bg-red-950/70", border: "border-red-700/60", text: "text-red-300", dot: "#FF0000" },
    email: { bg: "bg-indigo-950/70", border: "border-indigo-700/60", text: "text-indigo-300", dot: "#6366F1" },
};

// ── Date helpers ──────────────────────────────────────────────────────────────

function isoDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function calendarDays(year, month) {
    const firstDay = new Date(year, month, 1).getDay(); // 0=Sun
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days = [];
    // Padding before first
    for (let i = 0; i < firstDay; i++) days.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
        days.push(new Date(year, month, d));
    }
    return days;
}

function weekDays(anchorDate) {
    const start = new Date(anchorDate);
    start.setDate(start.getDate() - start.getDay()); // Monday? No, Sunday
    return Array.from({ length: 7 }, (_, i) => {
        const d = new Date(start);
        d.setDate(start.getDate() + i);
        return d;
    });
}

const WEEKDAY_LABELS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

// ── Event chip ────────────────────────────────────────────────────────────────

function EventChip({ event, onTooltip }) {
    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: event.id,
        data: { event },
    });

    const cfg = CHANNEL_COLORS[event.channel] ?? CHANNEL_COLORS.email;

    return (
        <div
            ref={setNodeRef}
            {...attributes}
            {...listeners}
            onMouseEnter={() => onTooltip(event)}
            onMouseLeave={() => onTooltip(null)}
            className={[
                "relative flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold truncate",
                "border cursor-grab active:cursor-grabbing select-none transition-opacity",
                cfg.bg, cfg.border, cfg.text,
                isDragging ? "opacity-30" : "hover:brightness-125",
            ].join(" ")}
        >
            <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{ background: cfg.dot }}
            />
            <span className="truncate">{event.topic.split(" ").slice(0, 2).join(" ")}</span>
        </div>
    );
}

// ── Day cell ──────────────────────────────────────────────────────────────────

function DayCell({ date, events, isToday, isGap, onTooltip, onAddDay, view }) {
    const { setNodeRef, isOver } = useDroppable({
        id: date ? isoDate(date) : "empty",
        disabled: !date,
    });

    if (!date) {
        return <div className="min-h-[80px]" />;
    }

    const dayEvents = events[isoDate(date)] ?? [];

    return (
        <div
            ref={setNodeRef}
            className={[
                "relative min-h-[80px] rounded-lg border p-1.5 transition-all duration-200 group",
                isToday ? "border-[#6366F1]/70 bg-[#6366F1]/5" : "border-[#2E2E2E] bg-[#1A1A1A]",
                isGap ? "border-amber-800/40 bg-amber-950/20" : "",
                isOver ? "border-[#6366F1]/60 bg-[#6366F1]/10" : "",
            ].join(" ")}
        >
            {/* Day number */}
            <div className="flex items-center justify-between mb-1">
                <span
                    className={[
                        "text-[11px] font-semibold w-5 h-5 flex items-center justify-center rounded-full",
                        isToday ? "bg-[#6366F1] text-white" : "text-[#9CA3AF]",
                    ].join(" ")}
                >
                    {date.getDate()}
                </span>

                {/* + button */}
                <button
                    onClick={() => onAddDay?.(date)}
                    className="opacity-0 group-hover:opacity-100 w-4 h-4 rounded flex items-center justify-center bg-[#2E2E2E] hover:bg-[#6366F1] text-[#6B7280] hover:text-white transition-all"
                >
                    <Plus size={9} />
                </button>
            </div>

            {/* Gap warning */}
            {isGap && dayEvents.length === 0 && (
                <div className="text-[9px] text-amber-400/80 leading-tight mt-1">
                    📭 Sem conteúdo
                </div>
            )}

            {/* Events */}
            <div className="space-y-0.5">
                {dayEvents.slice(0, view === "week" ? 8 : 3).map((ev) => (
                    <EventChip key={ev.id} event={ev} onTooltip={onTooltip} />
                ))}
                {view === "month" && dayEvents.length > 3 && (
                    <p className="text-[9px] text-[#6B7280] pl-1">+{dayEvents.length - 3} mais</p>
                )}
            </div>
        </div>
    );
}

// ── Tooltip ───────────────────────────────────────────────────────────────────

function EventTooltip({ event }) {
    const cfg = CHANNEL_COLORS[event.channel] ?? CHANNEL_COLORS.email;
    return (
        <div className="fixed top-4 right-4 z-50 bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-3 shadow-2xl max-w-[220px] animate-[fade-in_0.15s_ease-out]">
            <div className="flex items-center gap-1.5 mb-2">
                <span className="w-2 h-2 rounded-full" style={{ background: cfg.dot }} />
                <span className={`text-[10px] font-semibold capitalize ${cfg.text}`}>{event.channel}</span>
                <span className="text-[10px] text-[#6B7280] ml-auto">{event.time}</span>
            </div>
            <p className="text-xs text-[#F9FAFB] leading-snug">{event.topic}</p>
        </div>
    );
}

// ── Drag overlay chip ─────────────────────────────────────────────────────────

function DragChip({ event }) {
    const cfg = CHANNEL_COLORS[event.channel] ?? CHANNEL_COLORS.email;
    return (
        <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold border shadow-2xl ${cfg.bg} ${cfg.border} ${cfg.text}`}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.dot }} />
            {event.topic.split(" ").slice(0, 3).join(" ")}
        </div>
    );
}

// ── Calendar grid (monthly) ───────────────────────────────────────────────────

function MonthGrid({ year, month, eventsByDate, gapDates, tooltip, setTooltip, onAddDay }) {
    const days = calendarDays(year, month);
    const today = isoDate(new Date());

    return (
        <div>
            {/* Weekday headers */}
            <div className="grid grid-cols-7 gap-1 mb-1">
                {WEEKDAY_LABELS.map((d) => (
                    <div key={d} className="text-center text-[10px] font-medium text-[#4B5563] py-1">{d}</div>
                ))}
            </div>

            {/* Day cells */}
            <div className="grid grid-cols-7 gap-1">
                {days.map((date, i) => (
                    <DayCell
                        key={i}
                        date={date}
                        events={eventsByDate}
                        isToday={date ? isoDate(date) === today : false}
                        isGap={date ? gapDates.has(isoDate(date)) : false}
                        onTooltip={setTooltip}
                        onAddDay={onAddDay}
                        view="month"
                    />
                ))}
            </div>
        </div>
    );
}

// ── Week grid ─────────────────────────────────────────────────────────────────

function WeekGrid({ anchorDate, eventsByDate, gapDates, tooltip, setTooltip, onAddDay }) {
    const days = weekDays(anchorDate);
    const today = isoDate(new Date());

    return (
        <div>
            <div className="grid grid-cols-7 gap-1.5">
                {days.map((date, i) => (
                    <div key={i} className="flex flex-col gap-1">
                        <div className="text-center">
                            <p className="text-[10px] text-[#4B5563]">{WEEKDAY_LABELS[i]}</p>
                            <span
                                className={`text-xs font-semibold w-6 h-6 flex items-center justify-center rounded-full mx-auto ${isoDate(date) === today ? "bg-[#6366F1] text-white" : "text-[#9CA3AF]"
                                    }`}
                            >
                                {date.getDate()}
                            </span>
                        </div>
                        <DayCell
                            date={date}
                            events={eventsByDate}
                            isToday={isoDate(date) === today}
                            isGap={gapDates.has(isoDate(date))}
                            onTooltip={setTooltip}
                            onAddDay={onAddDay}
                            view="week"
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Main CalendarPage ─────────────────────────────────────────────────────────

export default function CalendarPage() {
    const navigate = useNavigate();
    const now = new Date();
    const [year, setYear] = useState(now.getFullYear());
    const [month, setMonth] = useState(now.getMonth());
    const [view, setView] = useState("month"); // "month" | "week"
    const [weekAnchor, setWeekAnchor] = useState(now);
    const [events, setEvents] = useState(MOCK_CALENDAR_EVENTS);
    const [tooltip, setTooltip] = useState(null);
    const [activeEvent, setActiveEvent] = useState(null);

    const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

    // Index events by dateStr
    const eventsByDate = useMemo(() => {
        const map = {};
        events.forEach((ev) => {
            if (!map[ev.dateStr]) map[ev.dateStr] = [];
            map[ev.dateStr].push(ev);
        });
        return map;
    }, [events]);

    // Gap detection: 3+ consecutive days without events in the current month's range
    const gapDates = useMemo(() => {
        const occupied = new Set(events.map((e) => e.dateStr));
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const gaps = new Set();
        let gapRun = 0;
        const runStart = [];

        for (let d = 1; d <= daysInMonth; d++) {
            const ds = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
            if (occupied.has(ds)) {
                gapRun = 0;
                runStart.length = 0;
            } else {
                gapRun++;
                runStart.push(ds);
                if (gapRun >= 3) runStart.forEach((s) => gaps.add(s));
            }
        }
        return gaps;
    }, [events, year, month]);

    function handleDragStart({ active }) {
        setActiveEvent(events.find((e) => e.id === active.id) ?? null);
    }

    function handleDragEnd({ active, over }) {
        setActiveEvent(null);
        if (!over) return;

        const newDateStr = over.id; // droppable id = dateStr
        setEvents((prev) =>
            prev.map((ev) =>
                ev.id === active.id
                    ? { ...ev, dateStr: newDateStr, date: new Date(newDateStr + "T12:00:00") }
                    : ev
            )
        );
    }

    function prevPeriod() {
        if (view === "month") {
            if (month === 0) { setYear(y => y - 1); setMonth(11); }
            else setMonth(m => m - 1);
        } else {
            const d = new Date(weekAnchor);
            d.setDate(d.getDate() - 7);
            setWeekAnchor(d);
        }
    }

    function nextPeriod() {
        if (view === "month") {
            if (month === 11) { setYear(y => y + 1); setMonth(0); }
            else setMonth(m => m + 1);
        } else {
            const d = new Date(weekAnchor);
            d.setDate(d.getDate() + 7);
            setWeekAnchor(d);
        }
    }

    function goToday() {
        setYear(now.getFullYear());
        setMonth(now.getMonth());
        setWeekAnchor(now);
    }

    function handleAddDay(date) {
        navigate("/pipeline");
    }

    const periodLabel = view === "month"
        ? `${MONTH_NAMES[month]} ${year}`
        : (() => {
            const days = weekDays(weekAnchor);
            const first = days[0], last = days[6];
            return `${first.getDate()} – ${last.getDate()} ${MONTH_NAMES[last.getMonth()]} ${last.getFullYear()}`;
        })();

    return (
        <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
            <div className="p-5 md:p-6 max-w-6xl mx-auto space-y-5 animate-[fade-in_0.25s_ease-out]">

                {/* Header */}
                <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div>
                        <h1 className="text-xl font-bold text-[#F9FAFB]">Calendário</h1>
                        <p className="text-xs text-[#6B7280] mt-0.5">Posts agendados — arraste para reagendar</p>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* View toggle */}
                        <div className="flex bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg p-0.5">
                            <button
                                onClick={() => setView("month")}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${view === "month" ? "bg-[#6366F1] text-white" : "text-[#9CA3AF] hover:text-[#F9FAFB]"
                                    }`}
                            >
                                <CalendarDays size={12} /> Mês
                            </button>
                            <button
                                onClick={() => setView("week")}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${view === "week" ? "bg-[#6366F1] text-white" : "text-[#9CA3AF] hover:text-[#F9FAFB]"
                                    }`}
                            >
                                <LayoutList size={12} /> Semana
                            </button>
                        </div>

                        {/* Navigation */}
                        <div className="flex items-center gap-1">
                            <button
                                onClick={prevPeriod}
                                className="w-8 h-8 flex items-center justify-center rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] text-[#9CA3AF] hover:bg-[#242424] transition-colors"
                            >
                                <ChevronLeft size={14} />
                            </button>

                            <button
                                onClick={goToday}
                                className="px-3 h-8 text-xs font-medium text-[#9CA3AF] bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg hover:bg-[#242424] transition-colors"
                            >
                                Hoje
                            </button>

                            <button
                                onClick={nextPeriod}
                                className="w-8 h-8 flex items-center justify-center rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] text-[#9CA3AF] hover:bg-[#242424] transition-colors"
                            >
                                <ChevronRight size={14} />
                            </button>
                        </div>

                        <span className="text-sm font-semibold text-[#F9FAFB] min-w-[160px] text-right">{periodLabel}</span>
                    </div>
                </div>

                {/* Channel legend */}
                <div className="flex gap-3 flex-wrap">
                    {Object.entries(CHANNEL_COLORS).map(([ch, cfg]) => (
                        <div key={ch} className="flex items-center gap-1.5 text-[10px] text-[#9CA3AF]">
                            <span className="w-2 h-2 rounded-full" style={{ background: cfg.dot }} />
                            <span className="capitalize">{ch === "twitter" ? "X" : ch}</span>
                        </div>
                    ))}
                    <div className="flex items-center gap-1.5 text-[10px] text-amber-400/80 ml-2">
                        <span className="w-2 h-2 rounded border border-amber-600/60 bg-amber-950/50" />
                        Lacuna de conteúdo
                    </div>
                </div>

                {/* Calendar grid */}
                <div className="bg-[#0F0F0F] rounded-xl border border-[#2E2E2E] p-3">
                    {view === "month" ? (
                        <MonthGrid
                            year={year}
                            month={month}
                            eventsByDate={eventsByDate}
                            gapDates={gapDates}
                            tooltip={tooltip}
                            setTooltip={setTooltip}
                            onAddDay={handleAddDay}
                        />
                    ) : (
                        <WeekGrid
                            anchorDate={weekAnchor}
                            eventsByDate={eventsByDate}
                            gapDates={gapDates}
                            tooltip={tooltip}
                            setTooltip={setTooltip}
                            onAddDay={handleAddDay}
                        />
                    )}
                </div>

                {/* Stats footer */}
                <div className="flex gap-6 text-xs text-[#6B7280]">
                    <span><strong className="text-[#F9FAFB]">{events.length}</strong> posts no período</span>
                    <span><strong className="text-amber-400">{gapDates.size}</strong> dias sem conteúdo</span>
                </div>
            </div>

            {/* Drag overlay */}
            <DragOverlay>
                {activeEvent && <DragChip event={activeEvent} />}
            </DragOverlay>

            {/* Tooltip */}
            {tooltip && <EventTooltip event={tooltip} />}
        </DndContext>
    );
}

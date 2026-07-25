export default function Skeleton({ className }: { className?: string }) {
    return (
        <div className={`animate-pulse bg-[#2D333B] rounded-lg ${className || 'w-full h-full'}`}></div>
    );
}

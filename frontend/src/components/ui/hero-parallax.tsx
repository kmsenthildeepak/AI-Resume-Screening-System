import React from "react";
import {
  motion,
  useScroll,
  useTransform,
  useSpring,
  useReducedMotion,
  MotionValue,
} from "motion/react";

export interface ProductCardItem {
  title: string;
  link: string;
  thumbnail: string;
  category?: string;
  description?: string;
}

export const HeroParallax = ({
  products,
  headerTitle = "AI-Powered Resume Screening System",
  headerSubtitle = "Screen resumes, match skills against job descriptions, and compare candidates using transparent, evidence-based ranking indicators.",
  dashboardUrl = "http://localhost:8501",
}: {
  products: ProductCardItem[];
  headerTitle?: string;
  headerSubtitle?: string;
  dashboardUrl?: string;
}) => {
  const firstRow = products.slice(0, 5);
  const secondRow = products.slice(5, 10);
  const thirdRow = products.slice(10, 15);
  const ref = React.useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });

  const springConfig = { stiffness: 300, damping: 30, bounce: 100 };

  const translateX = useSpring(
    useTransform(scrollYProgress, [0, 1], [0, shouldReduceMotion ? 0 : 600]),
    springConfig
  );
  const translateXReverse = useSpring(
    useTransform(scrollYProgress, [0, 1], [0, shouldReduceMotion ? 0 : -600]),
    springConfig
  );
  const rotateX = useSpring(
    useTransform(scrollYProgress, [0, 0.2], [shouldReduceMotion ? 0 : 15, 0]),
    springConfig
  );
  const opacity = useSpring(
    useTransform(scrollYProgress, [0, 0.2], [0.35, 1]),
    springConfig
  );
  const rotateZ = useSpring(
    useTransform(scrollYProgress, [0, 0.2], [shouldReduceMotion ? 0 : 12, 0]),
    springConfig
  );
  const translateY = useSpring(
    useTransform(scrollYProgress, [0, 0.2], [shouldReduceMotion ? 0 : -450, shouldReduceMotion ? 0 : 250]),
    springConfig
  );

  return (
    <div
      ref={ref}
      className="relative flex flex-col self-auto overflow-hidden bg-slate-950 py-16 antialiased [perspective:1000px] [transform-style:preserve-3d] min-h-[220vh] md:min-h-[260vh]"
    >
      <Header
        title={headerTitle}
        subtitle={headerSubtitle}
        dashboardUrl={dashboardUrl}
      />
      <motion.div
        style={{
          rotateX,
          rotateZ,
          translateY,
          opacity,
        }}
        className="w-full"
      >
        <motion.div className="mb-14 flex flex-row-reverse space-x-10 space-x-reverse">
          {firstRow.map((product) => (
            <ProductCard
              product={product}
              translate={translateX}
              key={product.title}
              dashboardUrl={dashboardUrl}
            />
          ))}
        </motion.div>
        <motion.div className="mb-14 flex flex-row space-x-10">
          {secondRow.map((product) => (
            <ProductCard
              product={product}
              translate={translateXReverse}
              key={product.title}
              dashboardUrl={dashboardUrl}
            />
          ))}
        </motion.div>
        <motion.div className="flex flex-row-reverse space-x-10 space-x-reverse">
          {thirdRow.map((product) => (
            <ProductCard
              product={product}
              translate={translateX}
              key={product.title}
              dashboardUrl={dashboardUrl}
            />
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
};

export const Header = ({
  title,
  subtitle,
  dashboardUrl,
}: {
  title: string;
  subtitle: string;
  dashboardUrl: string;
}) => {
  return (
    <div className="relative left-0 top-0 mx-auto max-w-7xl px-4 py-16 md:py-28 w-full z-20">
      <div className="inline-flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-400 mb-6 backdrop-blur-md">
        <span className="flex h-2 w-2 rounded-full bg-sky-400 animate-pulse" />
        Enterprise ATS Intelligence Engine
      </div>
      <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-5xl md:text-7xl">
        {title}
      </h1>
      <p className="mt-6 max-w-2xl text-base text-neutral-300 md:text-xl font-normal leading-relaxed">
        {subtitle}
      </p>

      <div className="mt-8 flex flex-wrap items-center gap-4">
        <a
          href={dashboardUrl}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all duration-200 hover:from-blue-500 hover:to-indigo-500 hover:shadow-blue-500/40 hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
          aria-label="Open Screening Dashboard (Streamlit ATS app on port 8501)"
        >
          <span>Open Screening Dashboard</span>
          <svg
            className="w-4 h-4 transition-transform group-hover:translate-x-1"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </a>
        <a
          href="#features"
          className="inline-flex items-center justify-center rounded-xl border border-neutral-700 bg-neutral-900/60 px-5 py-3.5 text-sm font-semibold text-neutral-300 backdrop-blur-sm transition-all duration-200 hover:bg-neutral-800 hover:text-white"
        >
          Explore Features
        </a>
      </div>

      <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 border-t border-neutral-800 text-neutral-400 text-xs sm:text-sm">
        <div>
          <span className="block text-white font-semibold text-lg sm:text-xl">100% Local</span>
          Private on-premise execution
        </div>
        <div>
          <span className="block text-white font-semibold text-lg sm:text-xl">Multi-format</span>
          PDF, DOCX, & TXT ingestion
        </div>
        <div>
          <span className="block text-white font-semibold text-lg sm:text-xl">TF-IDF + Cosine</span>
          Deterministic mathematical match
        </div>
        <div>
          <span className="block text-white font-semibold text-lg sm:text-xl">Transparent</span>
          Evidence quotes & skill coverage
        </div>
      </div>
    </div>
  );
};

export const ProductCard = ({
  product,
  translate,
  dashboardUrl,
}: {
  product: ProductCardItem;
  translate: MotionValue<number>;
  dashboardUrl: string;
}) => {
  return (
    <motion.div
      style={{
        x: translate,
      }}
      whileHover={{
        y: -15,
      }}
      key={product.title}
      className="group/product relative h-80 w-[24rem] sm:w-[28rem] flex-shrink-0 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/90 shadow-xl transition-shadow duration-300 hover:shadow-2xl hover:shadow-blue-500/10"
    >
      <a
        href={product.link || dashboardUrl}
        className="block h-full w-full relative overflow-hidden"
      >
        <img
          src={product.thumbnail}
          className="absolute inset-0 h-full w-full object-cover object-top transition duration-500 group-hover/product:scale-105 opacity-80 group-hover/product:opacity-100"
          alt={product.title}
          loading="lazy"
        />
        <div className="pointer-events-none absolute inset-0 h-full w-full bg-gradient-to-t from-black via-black/40 to-transparent opacity-90 transition-opacity group-hover/product:opacity-80" />
        <div className="absolute inset-x-0 bottom-0 p-5 flex flex-col justify-end">
          {product.category && (
            <span className="text-[11px] font-semibold tracking-wider uppercase text-sky-400 mb-1">
              {product.category}
            </span>
          )}
          <h2 className="text-lg font-bold text-white group-hover/product:text-blue-200 transition-colors">
            {product.title}
          </h2>
          {product.description && (
            <p className="mt-1 text-xs text-neutral-300 line-clamp-2">
              {product.description}
            </p>
          )}
        </div>
      </a>
    </motion.div>
  );
};

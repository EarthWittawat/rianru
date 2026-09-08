"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { listCourses, type Course } from "@/lib/api";

const STORAGE_KEY = "rianru.course";

type CourseState = {
  courses: Course[];
  course: string | undefined;
  setCourse: (code: string) => void;
};

const CourseContext = createContext<CourseState>({
  courses: [],
  course: undefined,
  setCourse: () => {},
});

/**
 * Which class the app is showing. Held here rather than in the URL because it
 * outlives navigation: you are studying one course across every page, not
 * choosing one per screen.
 */
export function CourseProvider({ children }: { children: ReactNode }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [chosen, setChosen] = useState<string | undefined>();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await listCourses();
        if (cancelled) return;
        setCourses(list);

        let remembered: string | null = null;
        try {
          remembered = window.localStorage.getItem(STORAGE_KEY);
        } catch {
          // Private windows and blocked site data both land here; a forgotten
          // choice is a smaller problem than a page that will not render.
        }
        const valid = list.some((course) => course.code === remembered);
        setChosen(valid && remembered ? remembered : list[0]?.code);
      } catch {
        if (!cancelled) setCourses([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<CourseState>(
    () => ({
      courses,
      course: chosen,
      setCourse: (code: string) => {
        setChosen(code);
        try {
          window.localStorage.setItem(STORAGE_KEY, code);
        } catch {
          // See above: remembering is a convenience, not a requirement.
        }
      },
    }),
    [courses, chosen],
  );

  return <CourseContext.Provider value={value}>{children}</CourseContext.Provider>;
}

export function useCourse() {
  return useContext(CourseContext);
}

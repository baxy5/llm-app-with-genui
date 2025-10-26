"use client";

const Error = ({ error }: { error: Error }) => {
  return (
    <main className="grid h-[100vh] place-items-center bg-gray-900 px-6 py-24 sm:py-32 lg:px-8">
      <div className="text-center">
        <p className="text-base font-semibold text-indigo-400">404</p>
        <h1 className="mt-4 text-5xl font-semibold tracking-tight text-balance text-white sm:text-7xl">
          <h2 className="text-2xl font-semibold mb-4">Something went wrong.</h2>
        </h1>
        <p className="mt-6 text-lg font-medium text-pretty text-red-500 sm:text-xl/8">
          {error.message || "Server is currently unavailable."}
        </p>
      </div>
    </main>
  );
};

export default Error;
